"""Run the redesigned UI with the real cloud ingest API and persistent SQLite."""
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from http.server import ThreadingHTTPServer
from beesky.cloud.server import make_handler
from beesky.cloud.store import CloudStore
from beesky.cloud.maintenance import MaintenanceService, MaintenanceScheduler

def handler(store, root, password=None):
    root = Path(root).resolve()
    base = make_handler(store, (root / 'index.html').read_bytes(), password)
    class Preview(base):
        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/' or path.startswith('/api/') or path in ('/login', '/logout', '/mcp'):
                return super().do_GET()
            if not self._viewer_gate(path):
                return
            target = (root / unquote(path).lstrip('/')).resolve()
            if root not in target.parents or not target.is_file():
                return self._send_json(404, {'error': 'not found'})
            self._send(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
    return Preview

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    store = CloudStore(str(root / 'work' / 'beesky-preview.db'))
    server = ThreadingHTTPServer(('127.0.0.1',int(os.environ.get('BEESKY_PREVIEW_PORT','8790'))),handler(store,root/'cloud-preview',os.environ.get('BEESKY_CLOUD_PASSWORD')))
    scheduler = MaintenanceScheduler(MaintenanceService(store))
    scheduler.start()
    print(f'BeeSky: http://127.0.0.1:{server.server_port} — monthly maintenance scheduler active', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        server.server_close()
        store.close()
