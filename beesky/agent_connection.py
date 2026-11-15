"""Resolve a Mine token to its server-owned agent and workshop, without scanning."""
from __future__ import annotations

import ipaddress
import json
import urllib.error
import urllib.parse
import urllib.request


class ConnectionError(ValueError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def connection_info(cloud_url: str, key: str) -> dict:
    parts=urllib.parse.urlsplit(cloud_url.strip())
    try:
        local=parts.hostname=='localhost' or ipaddress.ip_address(parts.hostname or '').is_loopback
    except ValueError:
        local=False
    if (not parts.hostname or parts.username or parts.password or parts.query or parts.fragment
            or parts.path not in ('','/') or parts.scheme not in ('http','https')
            or (parts.scheme=='http' and not local)):
        raise ConnectionError('Nhập địa chỉ Cloud HTTPS, ví dụ https://mine.beeskybase.com. Local có thể dùng HTTP.')
    key=key.strip()
    if not 20<=len(key)<=200 or any(c.isspace() for c in key):
        raise ConnectionError('Dán đầy đủ token được tạo trong mục Agent trên Mine.')
    req=urllib.request.Request(cloud_url.strip().rstrip('/')+'/api/agent/connection',
        headers={'Authorization':'Bearer '+key,'Accept':'application/json','User-Agent':'BeeSky-Agent'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),_NoRedirect())
    try:
        with opener.open(req,timeout=15) as response:
            raw=response.read(65537)
            if len(raw)>65536:raise ConnectionError('Phản hồi Cloud không hợp lệ.')
            data=json.loads(raw)
    except urllib.error.HTTPError as error:
        if error.code in (401,403):
            raise ConnectionError('Token không hợp lệ hoặc đã bị thu hồi. Tạo token mới trên Mine.') from None
        if error.code==404:
            raise ConnectionError('Cloud chưa hỗ trợ kiểm tra token. Kiểm tra địa chỉ hoặc cập nhật Cloud.') from None
        raise ConnectionError('Cloud chưa xác nhận kết nối. Vui lòng thử lại.') from None
    except (urllib.error.URLError,TimeoutError,OSError):
        raise ConnectionError('Không kết nối được Cloud. Kiểm tra mạng và địa chỉ Cloud.') from None
    except (ValueError,TypeError):
        raise ConnectionError('Phản hồi Cloud không hợp lệ.') from None
    if (not isinstance(data,dict) or not all(isinstance(data.get(k),str) and data[k]
            for k in ('agentId','agentName','siteId','siteName','organizationName'))):
        raise ConnectionError('Cloud chưa trả đủ thông tin agent và xưởng.')
    return {k:data[k] for k in ('agentId','agentName','siteId','siteName','organizationName')}
