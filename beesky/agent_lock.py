"""One running agent per saved config, including app and scheduled-task launches."""
from contextlib import contextmanager
from pathlib import Path
import os

@contextmanager
def agent_run_lock(config_path):
    path=Path(config_path).with_suffix('.run.lock')
    path.parent.mkdir(parents=True,exist_ok=True)
    file=path.open('a+b')
    locked=False
    try:
        file.seek(0,2)
        if file.tell()==0:file.write(b'0');file.flush()
        file.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            locked=True
        except OSError:
            raise RuntimeError('Agent đã chạy với cấu hình này. Dừng phiên hiện tại trước khi mở phiên mới.') from None
        yield
    finally:
        if locked:
            file.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(file.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(file.fileno(),fcntl.LOCK_UN)
        file.close()
