"""Monthly maintenance, immutable checklists, evidence and an in-process scheduler.

Dates use Vietnam time (UTC+7). SQLite is shared with CloudStore; all writes
use its lock and transactions. No browser needs to be open for scheduling.
"""
from __future__ import annotations
import base64
import calendar
import datetime as dt
import html
import json
import logging
import math
import re
import threading
import time
import uuid

VN = dt.timezone(dt.timedelta(hours=7))
TEMPLATES = {
    'air': ['Ghi nhiệt độ và hashrate trước bảo trì', 'Kiểm tra bụi, vệ sinh khe gió theo quy trình đã ngắt nguồn', 'Kiểm tra quạt, tiếng ồn và đầu nối', 'Kiểm tra dây điện, nguồn và điểm nóng', 'Chạy thử, ghi nhiệt độ và hashrate sau bảo trì'],
    'water': ['Ghi nhiệt độ và hashrate trước bảo trì', 'Kiểm tra rò rỉ, ống và đầu nối cấp/hồi', 'Kiểm tra bơm, bộ tản và thông số nước theo hướng dẫn thiết bị', 'Vệ sinh lọc và kiểm tra van theo quy trình đã cô lập', 'Chạy thử, kiểm tra rò rỉ và ghi thông số sau bảo trì'],
    'electrical': ['Ghi tải trạm và tải từng pha', 'Kiểm tra nhiệt độ tủ, dây và đầu nối', 'Kiểm tra nhãn nhánh, pha và dấu hiệu bất thường', 'Kiểm tra vệ sinh, tiếp địa theo quy trình của kỹ thuật viên', 'Ghi thông số sau kiểm tra và kiến nghị xử lý'],
}

class MaintenanceError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status

def text(value, label, maximum=500, required=False):
    if not isinstance(value, str):
        raise MaintenanceError(label + ' không hợp lệ.')
    value = value.strip()
    if (required and not value) or len(value) > maximum:
        raise MaintenanceError(label + ' bị thiếu hoặc quá dài.')
    return value

def integer(value, low, high, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value != int(value) or not low <= value <= high:
        raise MaintenanceError(label + ' không hợp lệ.')
    return int(value)

def today_vn():
    return dt.datetime.now(VN).date()

def month_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}', value):
        raise MaintenanceError('Tháng cần có dạng YYYY-MM.')
    try:
        return dt.date.fromisoformat(value + '-01')
    except ValueError:
        raise MaintenanceError('Tháng không hợp lệ.') from None

class MaintenanceService:
    def __init__(self, store):
        self.store = store
        with store._lock, store._db:
            store._db.executescript('''
                CREATE TABLE IF NOT EXISTS maintenance_schedules(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS maintenance_tickets(id TEXT PRIMARY KEY, schedule_id TEXT NOT NULL, period TEXT NOT NULL, data TEXT NOT NULL, UNIQUE(schedule_id,period));
                CREATE TABLE IF NOT EXISTS maintenance_photos(id TEXT PRIMARY KEY, ticket_id TEXT NOT NULL, item_id TEXT NOT NULL, stage TEXT NOT NULL, name TEXT NOT NULL, mime TEXT NOT NULL, created_at REAL NOT NULL, author TEXT NOT NULL, body BLOB NOT NULL);
                CREATE INDEX IF NOT EXISTS maintenance_photo_ticket ON maintenance_photos(ticket_id);
            ''')

    def _get(self, table, entity_id):
        row = self.store._db.execute('SELECT data FROM '+table+' WHERE id=?', (entity_id,)).fetchone()
        if not row:
            raise MaintenanceError('Không tìm thấy phiếu/lịch bảo trì.', 404)
        return json.loads(row['data'])

    def _photos(self, ticket_id):
        rows = self.store._db.execute('SELECT id,item_id,stage,name,mime,created_at,author FROM maintenance_photos WHERE ticket_id=? ORDER BY created_at,id', (ticket_id,)).fetchall()
        return [{**dict(row), 'url': '/api/maintenance/photos/'+row['id']} for row in rows]

    def _ticket(self, ticket_id):
        result = self._get('maintenance_tickets', ticket_id)
        result['photos'] = self._photos(ticket_id)
        return result

    def ticket(self, ticket_id):
        with self.store._lock:
            return self._ticket(ticket_id)

    def _write_ticket(self, ticket, actor, event):
        ticket.pop('photos', None)
        ticket['revision'] += 1
        ticket['updated_at'] = time.time()
        ticket['history'].append({'at': ticket['updated_at'], 'actor': actor, 'event': event})
        self.store._db.execute('UPDATE maintenance_tickets SET data=? WHERE id=?', (json.dumps(ticket, ensure_ascii=False), ticket['id']))
        return self._ticket(ticket['id'])

    def _check_revision(self, entity, body):
        if body.get('revision') != entity['revision']:
            raise MaintenanceError('Phiếu/lịch đã được sửa ở cửa sổ khác. Tải lại trước khi lưu.', 409)

    def _editable(self, ticket):
        if ticket['status'] not in ('open', 'in_progress'):
            raise MaintenanceError('Phiếu đang chờ xác nhận hoặc đã hoàn tất; không thể sửa checklist/ảnh.', 409)

    def save_schedule(self, body):
        site = text(body.get('site'), 'Xưởng', 120, True)
        site_name = text(body.get('siteName'), 'Tên xưởng', 160, True)
        name = text(body.get('name'), 'Tên quy trình', 160, True)
        owner = text(body.get('owner'), 'Người phụ trách', 120, True)
        actor = text(body.get('actor'), 'Người lưu', 120, True)
        start = month_date(body.get('startMonth'))
        if not 2020 <= start.year <= today_vn().year + 5:
            raise MaintenanceError('Tháng bắt đầu ngoài phạm vi hỗ trợ.')
        day = integer(body.get('day'), 1, 31, 'Ngày bảo trì')
        scope_type = body.get('scopeType')
        if scope_type not in ('site', 'rack', 'group', 'device'):
            raise MaintenanceError('Phạm vi bảo trì không hợp lệ.')
        scope_id = text(body.get('scopeId'), 'Đối tượng', 160, True)
        scope_name = text(body.get('scopeName'), 'Tên đối tượng', 240, True)
        raw_items = body.get('items')
        if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= 60:
            raise MaintenanceError('Checklist cần từ 1–60 hạng mục.')
        items = []
        for item in raw_items:
            if not isinstance(item, dict) or not isinstance(item.get('photoRequired', False), bool):
                raise MaintenanceError('Hạng mục không hợp lệ.')
            items.append({'id': uuid.uuid4().hex, 'title': text(item.get('title'), 'Hạng mục', 300, True), 'photoRequired': item.get('photoRequired', False)})
        with self.store._lock, self.store._db:
            old = self._get('maintenance_schedules', body['id']) if body.get('id') else None
            if old:
                self._check_revision(old, body)
                if old['site'] != site:
                    raise MaintenanceError('Không đổi xưởng của lịch đã tạo.')
            schedule = {'id': old['id'] if old else uuid.uuid4().hex, 'revision': old['revision']+1 if old else 1,
                        'site': site, 'siteName': site_name, 'name': name, 'owner': owner,
                        'startMonth': start.strftime('%Y-%m'), 'day': day, 'scopeType': scope_type,
                        'scopeId': scope_id, 'scopeName': scope_name, 'items': items,
                        'active': old['active'] if old else True, 'created_at': old['created_at'] if old else time.time(),
                        'updated_at': time.time(), 'updated_by': actor}
            self.store._db.execute('INSERT INTO maintenance_schedules(id,data) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data', (schedule['id'], json.dumps(schedule, ensure_ascii=False)))
        self.tick()
        return schedule

    def toggle_schedule(self, entity_id, body):
        actor = text(body.get('actor'), 'Người lưu', 120, True)
        with self.store._lock, self.store._db:
            schedule = self._get('maintenance_schedules', entity_id)
            self._check_revision(schedule, body)
            schedule.update(active=not schedule['active'], revision=schedule['revision']+1, updated_at=time.time(), updated_by=actor)
            self.store._db.execute('UPDATE maintenance_schedules SET data=? WHERE id=?', (json.dumps(schedule, ensure_ascii=False), entity_id))
        self.tick()
        return schedule

    def _targets(self, schedule, plan):
        site = schedule['site']
        devices = [d for d in plan.get('layout', {}).get('devices', []) if d.get('site') == site]
        scope = schedule['scopeType']
        if scope == 'rack':
            rack = next((r for r in plan.get('layout', {}).get('racks', []) if r.get('site') == site and r.get('id') == schedule['scopeId']), {})
            devices = [d for d in devices if d.get('id') in rack.get('slots', [])]
        elif scope == 'group':
            group = next((g for g in plan.get('groups', []) if g.get('site') == site and g.get('id') == schedule['scopeId']), {})
            devices = [d for d in devices if d.get('id') in group.get('memberIds', [])]
        elif scope == 'device':
            devices = [d for d in devices if d.get('id') == schedule['scopeId']]
        return [{key: d.get(key, '') for key in ('id', 'ip', 'model', 'serial', 'worker', 'customerOwner', 'customerId')} for d in devices]

    def tick(self, today=None):
        today = today or today_vn()
        with self.store._lock, self.store._db:
            raw = self.store._db.execute("SELECT value FROM settings WHERE key='power_plan'").fetchone()
            plan = (json.loads(raw['value']).get('data') or {}) if raw else {}
            schedules = [json.loads(row['data']) for row in self.store._db.execute('SELECT data FROM maintenance_schedules')]
            for schedule in schedules:
                if not schedule['active']:
                    continue
                period_date = month_date(schedule['startMonth'])
                while period_date.replace(day=1) <= today.replace(day=1):
                    period = period_date.strftime('%Y-%m')
                    if not self.store._db.execute('SELECT 1 FROM maintenance_tickets WHERE schedule_id=? AND period=?', (schedule['id'], period)).fetchone():
                        due = dt.date(period_date.year, period_date.month, min(schedule['day'], calendar.monthrange(period_date.year, period_date.month)[1]))
                        ticket = {'id': uuid.uuid4().hex, 'revision': 1, 'scheduleId': schedule['id'], 'scheduleRevision': schedule['revision'],
                                  'period': period, 'due': due.isoformat(), 'name': schedule['name'], 'site': schedule['site'], 'siteName': schedule['siteName'],
                                  'scopeName': schedule['scopeName'], 'scopeType': schedule['scopeType'], 'scopeId': schedule['scopeId'],
                                  'targets': self._targets(schedule, plan), 'owner': schedule['owner'], 'status': 'open', 'notes': '', 'cost': 0,
                                  'created_at': time.time(), 'updated_at': time.time(), 'performed_by': '', 'submitted_at': None, 'approved_by': '', 'approved_at': None,
                                  'items': [{**item, 'result': '', 'notes': ''} for item in schedule['items']], 'repairs': [],
                                  'history': [{'at': time.time(), 'actor': 'Lịch máy chủ', 'event': 'Tạo phiếu tháng '+period}]}
                        self.store._db.execute('INSERT INTO maintenance_tickets(id,schedule_id,period,data) VALUES(?,?,?,?)', (ticket['id'], schedule['id'], period, json.dumps(ticket, ensure_ascii=False)))
                    period_date = dt.date(period_date.year+int(period_date.month==12), period_date.month%12+1, 1)

    def listing(self, month, site=None):
        month_date(month)
        self.tick()
        with self.store._lock:
            schedules = [json.loads(r['data']) for r in self.store._db.execute('SELECT data FROM maintenance_schedules')]
            tickets = [self._ticket(r['id']) for r in self.store._db.execute('SELECT id FROM maintenance_tickets WHERE period=? ORDER BY rowid DESC', (month,))]
        if site:
            schedules = [s for s in schedules if s['site'] == site]
            tickets = [t for t in tickets if t['site'] == site]
        today = today_vn().isoformat()
        summary = {'total': len(tickets), 'completed': sum(t['status']=='completed' for t in tickets),
                   'overdue': sum(t['due']<today and t['status']!='completed' for t in tickets),
                   'failed': sum(i['result']=='fail' for t in tickets for i in t['items']), 'cost': sum(t['cost'] for t in tickets)}
        return {'month': month, 'schedules': schedules, 'tickets': tickets, 'summary': summary, 'today': today, 'templates': TEMPLATES}

    def update_ticket(self, ticket_id, body):
        actor = text(body.get('actor'), 'Người thực hiện/xác nhận', 120, True)
        action = body.get('action', 'save')
        with self.store._lock, self.store._db:
            ticket = self._ticket(ticket_id)
            self._check_revision(ticket, body)
            if action in ('save', 'submit'):
                self._editable(ticket)
                updates = body.get('items')
                if not isinstance(updates, list) or len(updates) != len(ticket['items']) or {i.get('id') for i in updates if isinstance(i, dict)} != {i['id'] for i in ticket['items']}:
                    raise MaintenanceError('Checklist không khớp với phiếu gốc.')
                mapped = {item['id']: item for item in updates}
                for item in ticket['items']:
                    update = mapped[item['id']]
                    if update.get('result') not in ('', 'pass', 'fail', 'na'):
                        raise MaintenanceError('Kết quả checklist không hợp lệ.')
                    item.update(result=update['result'], notes=text(update.get('notes', ''), 'Ghi chú', 2000))
                ticket.update(notes=text(body.get('notes', ''), 'Ghi chú phiếu', 4000), cost=integer(body.get('cost', 0), 0, 10**12, 'Chi phí'), performed_by=actor, status='in_progress')
                if action == 'submit':
                    for item in ticket['items']:
                        if not item['result'] or (item['result']=='fail' and not item['notes']):
                            raise MaintenanceError('Điền đủ checklist; mục Không đạt cần ghi rõ lỗi.')
                        if item['result']=='na' and not item['notes']:
                            raise MaintenanceError('Mục Không áp dụng cần ghi lý do.')
                        if item['photoRequired'] and item['result']!='na' and not any(p['item_id']==item['id'] for p in ticket['photos']):
                            raise MaintenanceError('Thiếu ảnh minh chứng ở hạng mục bắt buộc.')
                    ticket.update(status='pending', submitted_at=time.time())
                event = 'Gửi xác nhận' if action=='submit' else 'Lưu nháp checklist'
            elif action == 'approve':
                if ticket['status']!='pending':
                    raise MaintenanceError('Chỉ xác nhận phiếu đang chờ duyệt.', 409)
                ticket.update(status='completed', approved_by=actor, approved_at=time.time())
                event = 'Xác nhận hoàn tất'
            elif action == 'return':
                if ticket['status']!='pending':
                    raise MaintenanceError('Chỉ trả lại phiếu đang chờ xác nhận.', 409)
                reason = text(body.get('reason'), 'Lý do trả lại', 1000, True)
                ticket.update(status='in_progress', submitted_at=None)
                event = 'Yêu cầu bổ sung: '+reason
            else:
                raise MaintenanceError('Thao tác không hợp lệ.')
            return self._write_ticket(ticket, actor, event)

    def add_photo(self, ticket_id, body):
        actor = text(body.get('actor'), 'Người chụp', 120, True)
        name = text(body.get('name', 'anh.jpg'), 'Tên ảnh', 160, True)
        stage = body.get('stage')
        if stage not in ('before', 'after'):
            raise MaintenanceError('Chọn ảnh trước hoặc sau bảo trì.')
        try:
            if not isinstance(body.get('data'), str) or len(body['data']) > 5700000:
                raise ValueError()
            blob = base64.b64decode(body['data'], validate=True)
        except (ValueError, TypeError):
            raise MaintenanceError('Ảnh không hợp lệ hoặc quá lớn.') from None
        mime = 'image/jpeg' if blob.startswith(b'\xff\xd8\xff') else 'image/png' if blob.startswith(b'\x89PNG\r\n\x1a\n') else 'image/webp' if blob[:4]==b'RIFF' and blob[8:12]==b'WEBP' else None
        if not mime or not 10 <= len(blob) <= 4*1024*1024:
            raise MaintenanceError('Chỉ nhận JPEG, PNG, WebP tối đa 4 MB.')
        with self.store._lock, self.store._db:
            ticket = self._ticket(ticket_id)
            self._check_revision(ticket, body)
            self._editable(ticket)
            if not any(i['id']==body.get('itemId') for i in ticket['items']):
                raise MaintenanceError('Hạng mục không thuộc phiếu.')
            if len(ticket['photos']) >= 120 or sum(p['item_id']==body['itemId'] for p in ticket['photos'])>=8:
                raise MaintenanceError('Tối đa 8 ảnh mỗi mục và 120 ảnh mỗi phiếu.')
            entity_id = uuid.uuid4().hex
            self.store._db.execute('INSERT INTO maintenance_photos VALUES(?,?,?,?,?,?,?,?,?)', (entity_id, ticket_id, body['itemId'], stage, name, mime, time.time(), actor, blob))
            return self._write_ticket(ticket, actor, 'Thêm ảnh '+('trước' if stage=='before' else 'sau')+' · '+name)

    def delete_photo(self, ticket_id, photo_id, body):
        actor = text(body.get('actor'), 'Người xóa', 120, True)
        with self.store._lock, self.store._db:
            ticket = self._ticket(ticket_id)
            self._check_revision(ticket, body)
            self._editable(ticket)
            if not any(p['id']==photo_id for p in ticket['photos']):
                raise MaintenanceError('Ảnh không thuộc phiếu.', 404)
            self.store._db.execute('DELETE FROM maintenance_photos WHERE id=? AND ticket_id=?', (photo_id, ticket_id))
            return self._write_ticket(ticket, actor, 'Xóa ảnh '+photo_id)

    def photo(self, photo_id):
        with self.store._lock:
            row = self.store._db.execute('SELECT mime,body FROM maintenance_photos WHERE id=?', (photo_id,)).fetchone()
            if not row:
                raise MaintenanceError('Không tìm thấy ảnh.', 404)
            return row['mime'], bytes(row['body'])

    def create_repair(self, ticket_id, body):
        actor = text(body.get('actor'), 'Kỹ thuật viên', 120, True)
        with self.store._lock, self.store._db:
            ticket = self._ticket(ticket_id)
            self._check_revision(ticket, body)
            if ticket['status']=='completed':
                raise MaintenanceError('Phiếu hoàn tất đã khóa.', 409)
            item = next((i for i in ticket['items'] if i['id']==body.get('itemId')), None)
            device = next((d for d in ticket['targets'] if d['id']==body.get('deviceId')), None)
            if not item or item['result']!='fail' or not device or not device.get('ip'):
                raise MaintenanceError('Chọn hạng mục Không đạt và máy trong phạm vi phiếu; lưu nháp trước khi tạo phiếu sửa.')
            if any(r['itemId']==item['id'] and r['deviceId']==device['id'] for r in ticket['repairs']):
                raise MaintenanceError('Máy đã có phiếu sửa cho lỗi này.', 409)
            cost = integer(body.get('cost', 0), 0, 10**12, 'Chi phí sửa')
            repair_id = self.store._insert_repair(None, ticket['site'], device['ip'], device.get('serial'), time.time(), 'manual', item['title'], 'Bảo trì '+ticket['id']+' · '+ticket['period']+'\n'+item['notes'], cost, actor)
            ticket['repairs'].append({'id': repair_id, 'itemId': item['id'], 'deviceId': device['id'], 'ip': device['ip'], 'cost': cost})
            return self._write_ticket(ticket, actor, 'Tạo phiếu sửa #'+str(repair_id)+' · '+device['ip'])

    def report(self, month, site=None):
        data = self.listing(month, site)
        esc = lambda value: html.escape(str(value), quote=True)
        labels = {'open':'Chưa làm', 'in_progress':'Đang làm', 'pending':'Chờ xác nhận', 'completed':'Hoàn tất', 'pass':'Đạt', 'fail':'Không đạt', 'na':'Không áp dụng', '':'Chưa kiểm tra'}
        s = data['summary']
        out = ['<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Báo cáo bảo trì '+esc(month)+'</title><style>body{font:14px Arial,sans-serif;color:#18202e;max-width:1000px;margin:32px auto;padding:16px}h1{font-size:24px}h2{font-size:19px}table{width:100%;border-collapse:collapse}td,th{border:1px solid #ccc;padding:8px;text-align:left;vertical-align:top}img{max-width:240px;max-height:180px;object-fit:contain}figure{display:inline-block;margin:8px}small{display:block;color:#526070}.ticket{margin-top:32px;border-top:2px solid #333}.item{break-inside:avoid;margin:20px 0}p{white-space:pre-wrap}button{padding:10px 16px}@media print{button{display:none}.ticket{break-before:page}body{margin:0;max-width:none}a{color:inherit;text-decoration:none}}@page{size:A4;margin:15mm}</style><button onclick="window.print()">In / Lưu PDF</button><h1>BeeSky · Báo cáo bảo trì tháng '+esc(month)+'</h1><p>Ngày lập: '+esc(today_vn())+' · Giờ Việt Nam (UTC+7)</p><p>Tổng phiếu: '+str(s['total'])+' · Hoàn tất: '+str(s['completed'])+' · Quá hạn: '+str(s['overdue'])+' · Hạng mục không đạt: '+str(s['failed'])+'</p><p>Chi phí ghi trên phiếu bảo trì: '+f"{s['cost']:,}"+' VNĐ (không cộng lại chi phí phiếu sửa liên kết).</p><p>Người thực hiện/xác nhận được nhập thủ công trong workspace quản trị chung.</p>']
        for t in data['tickets']:
            sample = any(str(d.get('serial', '')).startswith('DEMO-') for d in t['targets'])
            if sample:
                out += ['<p><strong>Phiếu sau đây dùng danh sách máy mẫu; chưa phải bằng chứng bảo trì máy thực tế.</strong></p>']
            out += ['<section class="ticket"><h2>'+esc(t['name'])+' · '+esc(t['period'])+'</h2><p>Mã: '+esc(t['id'])+'<br>Xưởng: '+esc(t['siteName'])+' · Đối tượng: '+esc(t['scopeName'])+'<br>Hạn: '+esc(t['due'])+' · Trạng thái: '+esc(labels[t['status']])+'<br>Phụ trách: '+esc(t['owner'])+' · Thực hiện: '+esc(t['performed_by'])+'<br>Xác nhận: '+esc(t['approved_by'])+' · '+esc(dt.datetime.fromtimestamp(t['approved_at'], VN).strftime('%d/%m/%Y %H:%M:%S') if t['approved_at'] else 'Chưa xác nhận')+'<br>Chi phí: '+f"{t['cost']:,}"+' VNĐ</p><p>'+esc(t['notes'])+'</p><details open><summary>Máy trong phạm vi tại thời điểm tạo phiếu ('+str(len(t['targets']))+')</summary><table><tr><th>IP / Serial</th><th>Model</th><th>Khách / Worker</th></tr>']
            for d in t['targets']:
                out += ['<tr><td>'+esc(d['ip'])+'<small>'+esc(d['serial'])+'</small></td><td>'+esc(d['model'])+'</td><td>'+esc(d.get('customerOwner') or d.get('customerId') or '')+'<small>'+esc(d.get('worker') or '')+'</small></td></tr>']
            out += ['</table></details>']
            for item in t['items']:
                out += ['<div class="item"><h3>'+esc(item['title'])+' — '+esc(labels[item['result']])+'</h3><p>'+esc(item['notes'])+'</p>']
                for p in t['photos']:
                    if p['item_id']==item['id']:
                        out += ['<figure><img src="'+esc(p['url'])+'" alt="'+esc(p['name'])+'"><figcaption>'+('Trước' if p['stage']=='before' else 'Sau')+' · '+esc(p['author'])+' · '+esc(dt.datetime.fromtimestamp(p['created_at'],VN).strftime('%d/%m/%Y %H:%M:%S'))+'</figcaption></figure>']
                out += ['</div>']
            out += ['<h3>Phiếu sửa liên kết</h3>']
            for r in t['repairs']:
                out += ['<p>#'+str(r['id'])+' · '+esc(r['ip'])+' · '+f"{r['cost']:,}"+' VNĐ</p>']
            out += ['<details open><summary>Lịch sử thao tác</summary>']
            for event in t['history']:
                out += ['<p>'+esc(dt.datetime.fromtimestamp(event['at'],VN).strftime('%d/%m/%Y %H:%M:%S'))+' · '+esc(event['actor'])+' · '+esc(event['event'])+'</p>']
            out += ['</details></section>']
        if not data['tickets']:
            out += ['<p>Không có phiếu trong tháng/phạm vi đã chọn.</p>']
        return ''.join(out)+'</html>'

class MaintenanceScheduler:
    def __init__(self, service, interval=60):
        self.service = service
        self.interval = interval
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, name='maintenance-scheduler', daemon=True)
    def start(self):
        self.thread.start()
    def _run(self):
        while not self.stop_event.is_set():
            try:
                self.service.tick()
            except Exception:
                logging.exception('Maintenance scheduler failed; retry next interval')
            self.stop_event.wait(self.interval)
    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=5)
