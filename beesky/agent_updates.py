"""Verified whole-application updates. No token is stored in an update job.

The installer replaces Flutter, its assets and both engines together. A copied
helper lives outside the installation, waits for the UI to exit, stops only the
authenticated worker, and restores its previous running state afterwards.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from . import __version__
from .agent_lock import agent_run_lock
from .agent_runtime import runtime_path, runtime_status, stop_agent
from .core import updater


def update_root(config):
    return Path(config).resolve().parent / 'agent-updates'


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def last_result(config):
    try:
        data = json.loads((update_root(config) / 'last-update.json').read_text(encoding='utf-8'))
        return {key: data[key] for key in ('phase', 'message', 'version', 'time') if key in data}
    except (OSError, ValueError, TypeError):
        return None


def _result(config, phase, message, version=None):
    _write(update_root(config) / 'last-update.json',
           {'phase': phase, 'message': message, 'version': version, 'time': time.time()})


def check_update(config, url_base=None):
    result = updater.check(url_base)
    message = ('Có bản Agent mới.' if result['update_available'] else 'Agent đang dùng bản mới nhất.')
    if not result['ok']:
        message = ('Kênh cập nhật chưa được thiết lập. Cài bản Agent mới từ Mine.'
                   if not result['enabled'] else
                   'Chưa kiểm tra được bản mới. Kiểm tra mạng rồi thử lại; Agent vẫn tiếp tục chạy.')
    entry = updater._find_entry(result['manifest'] or {}, f"BeeSkyAgentSetup-{result['latest']}.exe")
    if result['ok'] and entry is None:
        result['ok'] = False
        message = 'Bản phát hành đang được chuẩn bị. Thử kiểm tra lại sau ít phút.'
    return {'ok': result['ok'], 'current': __version__, 'latest': result['latest'],
            'available': result['ok'] and result['update_available'],
            'message': message, 'previous': last_result(config)}


def _digest(file):
    digest = hashlib.sha256()
    with file.open('rb') as stream:
        while chunk := stream.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def _entry(result):
    version = result['latest']
    if not re.fullmatch(r'\d+\.\d+\.\d+', str(version)):
        raise ValueError('Phiên bản phát hành không hợp lệ.')
    entry = updater._find_entry(result['manifest'], f'BeeSkyAgentSetup-{version}.exe')
    if (not entry or type(entry.get('size')) is not int or not 0 < entry['size'] < 512 * 1024 * 1024
            or not re.fullmatch(r'[a-fA-F0-9]{64}', str(entry.get('sha256', '')))
            or not isinstance(entry.get('url'), str)):
        raise ValueError('Bản phát hành chưa có bộ cài Agent hợp lệ. Thử lại sau.')
    return entry


def _download(entry, target, progress):
    import urllib.request
    request = urllib.request.Request(entry['url'], headers={'User-Agent': 'BeeSky-Agent-Updater'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    digest, count, previous = hashlib.sha256(), 0, -1
    with opener.open(request, timeout=20) as response, target.open('xb') as file:
        while chunk := response.read(65536):
            count += len(chunk)
            if count > entry['size']:
                raise ValueError('Bộ cài tải về không khớp bản phát hành. Chưa thay đổi Agent.')
            file.write(chunk)
            digest.update(chunk)
            percent = count * 100 // entry['size']
            if percent != previous:
                progress({'progress': percent, 'message': f'Đang tải bản mới… {percent}%'})
                previous = percent
    if count != entry['size'] or digest.hexdigest() != entry['sha256'].lower():
        raise ValueError('Bộ cài tải về chưa đầy đủ hoặc không hợp lệ. Chưa thay đổi Agent.')


def _spawn(args, cwd=None):
    options = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL,
               'stderr': subprocess.DEVNULL, 'close_fds': True, 'cwd': cwd}
    if os.name == 'nt':
        options['creationflags'] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options['start_new_session'] = True
    return subprocess.Popen(args, **options)


def prepare_update(config, ui_pid, progress=lambda data: None, url_base=None):
    config = Path(config).resolve()
    if os.name != 'nt' or not getattr(sys, 'frozen', False):
        raise ValueError('Cập nhật trong ứng dụng chỉ có trên bản Agent dành cho Windows.')
    install_dir = Path(sys.executable).resolve().parent
    if not (install_dir / 'beesky_agent_app.exe').is_file() or ui_pid <= 0:
        raise ValueError('Không xác định được ứng dụng Agent. Cài lại bản Agent từ Mine.')
    with agent_run_lock(update_root(config) / 'update.json'):
        previous = last_result(config)
        if previous and previous.get('phase') in ('prepared', 'installing') and time.time() - previous.get('time', 0) < 600:
            raise ValueError('Một lượt cập nhật đang được xử lý. Chờ Agent mở lại.')
        # Fail before downloading/stopping the worker if the installation is not writable.
        with tempfile.TemporaryFile(dir=install_dir):
            pass
        progress({'message': 'Đang xác nhận bản phát hành…'})
        result = updater.check(url_base)
        if not result['ok'] or not result['update_available']:
            raise ValueError('Chưa có bản mới đã được xác nhận. Bấm Kiểm tra lại để cập nhật trạng thái.')
        entry = _entry(result)
        directory = Path(tempfile.mkdtemp(prefix='update-', dir=update_root(config)))
        installer = directory / entry['name']
        try:
            _download(entry, installer, progress)
            # Recheck the signed source in the helper, not just a hash from a job file.
            base = result['url_base']
            manifest = updater._fetch(base + updater.MANIFEST_NAME)
            signature = updater._fetch(base + updater.SIG_NAME)
            if not updater.verify_signature(manifest, signature) or json.loads(manifest) != result['manifest']:
                raise ValueError('Bản phát hành vừa thay đổi. Chưa cập nhật; kiểm tra lại bản mới.')
            (directory / updater.MANIFEST_NAME).write_bytes(manifest)
            (directory / updater.SIG_NAME).write_bytes(signature)
            helper = directory / 'beesky-update-helper.exe'
            shutil.copyfile(sys.executable, helper)
            job = directory / 'update-job.json'
            _write(job, {'config': str(config), 'directory': str(install_dir), 'uiPid': ui_pid})
            _result(config, 'prepared', 'Đã tải và xác nhận bộ cài. Đang chờ Agent đóng cửa sổ.', result['latest'])
            process = _spawn([str(helper), 'update-install', '--config', str(config), '--job', str(job)])
            for _ in range(150):
                if (directory / 'helper-ready').is_file():
                    break
                if process.poll() is not None:
                    raise ValueError('Chưa mở được trình cập nhật. Agent hiện tại vẫn được giữ nguyên.')
                time.sleep(.1)
            else:
                process.terminate()
                process.wait(timeout=5)
                raise ValueError('Trình cập nhật khởi động quá lâu. Agent vẫn chạy; thử lại sau.')
            return {'ok': True, 'ready': True, 'message': 'Đã tải xong. Agent sẽ cập nhật và tự mở lại.', 'version': result['latest']}
        except Exception:
            installer.unlink(missing_ok=True)
            _result(config, 'failed', 'Chưa tải được bản cập nhật. Agent hiện tại vẫn được giữ nguyên.')
            raise


def _wait_ui(pid, timeout=90):
    if os.name != 'nt':
        raise ValueError('Cập nhật này dành cho Windows.')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x00100000, False, pid)
    if not handle:
        if ctypes.get_last_error() == 87:  # process already exited
            return True
        raise OSError('Không xác nhận được cửa sổ Agent đã đóng.')
    try:
        return kernel.WaitForSingleObject(handle, timeout * 1000) == 0
    finally:
        kernel.CloseHandle(handle)


def install_update(config, job_path):
    config, job_path = Path(config).resolve(), Path(job_path).resolve()
    if (job_path.name != 'update-job.json' or job_path.parent.parent != update_root(config)
            or Path(sys.executable).resolve().parent != job_path.parent):
        raise ValueError('Không nhận diện được phiên cập nhật.')
    (job_path.parent / 'helper-ready').write_text(str(os.getpid()), encoding='ascii')
    # Serialise helpers and preparations, including two UI windows.
    lock = update_root(config) / 'update.json'
    for attempt in range(50):
        try:
            with agent_run_lock(lock):
                return _install_locked(config, job_path)
        except RuntimeError:
            if attempt == 49:
                raise
            time.sleep(.1)


def _install_locked(config, job_path):
    job = json.loads(job_path.read_text(encoding='utf-8'))
    root = Path(job['directory']).resolve()
    app, engine = root / 'beesky_agent_app.exe', root / 'beesky-agent.exe'
    version, reopen, resume, success, restart_failed = None, False, False, False, False
    try:
        if Path(job['config']).resolve() != config or not app.is_file() or not engine.is_file() or root == job_path.parent:
            raise ValueError('Thông tin cài đặt không hợp lệ.')
        if not _wait_ui(int(job['uiPid'])):
            raise ValueError('Agent chưa đóng cửa sổ nên đã hủy cập nhật. Đóng các cửa sổ Agent rồi thử lại.')
        reopen = True
        manifest = (job_path.parent / updater.MANIFEST_NAME).read_bytes()
        signature = (job_path.parent / updater.SIG_NAME).read_bytes()
        if not updater.verify_signature(manifest, signature):
            raise ValueError('Bản cập nhật không còn hợp lệ. Agent chưa được thay đổi.')
        data = json.loads(manifest)
        version = data['version']
        entry = _entry({'latest': version, 'manifest': data})
        installer = job_path.parent / entry['name']
        if installer.stat().st_size != entry['size'] or _digest(installer) != entry['sha256'].lower():
            raise ValueError('Bộ cài đã thay đổi. Agent chưa được cập nhật.')
        resume = runtime_status(config)['running']
        if runtime_path(config).exists() and not resume:
            raise ValueError('Chưa xác nhận được tiến trình chạy ngầm. Mở Agent và làm mới trạng thái trước khi cập nhật.')
        _result(config, 'installing', 'Đang cài bản Agent mới…', version)
        if not stop_agent(config)['ok']:
            raise ValueError('Chưa dừng được Agent nên chưa cài bản mới. Mở nhật ký để kiểm tra.')
        # Show installer progress; never kill a partially completed installation
        # or resume the worker until the installer actually exits.
        result = subprocess.run([str(installer), '/SILENT', '/SUPPRESSMSGBOXES', '/SP-',
                                 '/NORESTART', '/CLOSEAPPLICATIONS', f'/DIR={root}',
                                 f'/BEESKYCONFIG={config}',
                                 f'/LOG={job_path.parent / "installer.log"}'])
        if result.returncode not in (0, 3010):
            raise ValueError('Cài bản mới chưa thành công. Cấu hình vẫn được giữ; xem nhật ký cập nhật để thử lại.')
        observed = subprocess.run([str(engine), 'version'], capture_output=True, timeout=20)
        if observed.returncode != 0 or json.loads(observed.stdout).get('version') != version:
            raise ValueError('Chưa xác nhận được phiên bản sau khi cài. Mở Agent để kiểm tra.')
        success = True
        return True
    except Exception as error:
        message = str(error) if isinstance(error, ValueError) else 'Cập nhật chưa hoàn tất. Cấu hình vẫn được giữ; thử lại hoặc xem nhật ký cập nhật.'
        _result(config, 'failed', message, version)
        return False
    finally:
        if reopen:
            if resume:
                try:
                    _spawn([str(engine), 'run', '--background', '--config', str(config)], cwd=root)
                except OSError:
                    restart_failed = True
                    _result(config, 'failed', 'Chưa mở lại được bộ chạy Agent. Bấm Bắt đầu Agent để thử lại.', version)
            try:
                _spawn([str(app)], cwd=root)
            except OSError:
                restart_failed = True
                _result(config, 'failed', 'Chưa mở lại được cửa sổ Agent. Mở BeeSky Agent từ Start để kiểm tra.', version)
            if success and not restart_failed:
                _result(config, 'complete', f'Đã cập nhật Agent lên {version}.', version)
