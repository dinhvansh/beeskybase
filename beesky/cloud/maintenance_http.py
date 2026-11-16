"""Authenticated HTTP adapter for maintenance endpoints."""
import re
from urllib.parse import parse_qs, urlparse
from .maintenance import MaintenanceError, today_vn

def handle_maintenance(handler, service):
    parsed = urlparse(handler.path)
    path = parsed.path
    query = parse_qs(parsed.query)
    try:
        if handler.command == 'GET':
            month = query.get('month', [today_vn().strftime('%Y-%m')])[0]
            site = query.get('site', [None])[0] or None
            if path == '/api/maintenance':
                return handler._send_json(200, service.listing(month, site))
            if path == '/api/maintenance/report':
                return handler._send(200, service.report(month, site).encode('utf-8'), 'text/html; charset=utf-8', {'Cache-Control':'no-store'})
            match = re.fullmatch(r'/api/maintenance/tickets/([0-9a-f]{32})', path)
            if match:
                return handler._send_json(200, service.ticket(match[1]))
            match = re.fullmatch(r'/api/maintenance/photos/([0-9a-f]{32})', path)
            if match:
                mime, blob = service.photo(match[1])
                return handler._send(200, blob, mime, {'X-Content-Type-Options':'nosniff', 'Cache-Control':'private, no-store'})
        elif handler.command == 'POST':
            body = handler._read_json_body()
            if body is None:
                raise MaintenanceError('Dữ liệu gửi lên không hợp lệ.')
            if path == '/api/maintenance/schedules':
                return handler._send_json(200, service.save_schedule(body))
            match = re.fullmatch(r'/api/maintenance/schedules/([0-9a-f]{32})/toggle', path)
            if match:
                return handler._send_json(200, service.toggle_schedule(match[1], body))
            match = re.fullmatch(r'/api/maintenance/tickets/([0-9a-f]{32})(/photos|/repairs|/photos/([0-9a-f]{32})/delete)?', path)
            if match:
                ticket_id, action, photo_id = match.groups()
                if action == '/photos':
                    result = service.add_photo(ticket_id, body)
                elif action == '/repairs':
                    result = service.create_repair(ticket_id, body)
                elif photo_id:
                    result = service.delete_photo(ticket_id, photo_id, body)
                else:
                    result = service.update_ticket(ticket_id, body)
                return handler._send_json(200, result)
        handler._send_json(404, {'error':'Không tìm thấy chức năng bảo trì.'})
    except MaintenanceError as exc:
        handler._send_json(exc.status, {'error':str(exc)})
