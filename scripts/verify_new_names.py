# -*- coding: utf-8 -*-
import urllib.request
import json
import ssl
import sys
import base64

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Check FileBrowser API
print("=== 1. FILEBROWSER CHECK ===")
try:
    req = urllib.request.Request(
        'https://178.140.8.56:34501/apps/fb/api/login',
        data=json.dumps({'username': 'admin', 'password': '12345678'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
        tok = r.read().decode()
    res_req = urllib.request.Request('https://178.140.8.56:34501/apps/fb/api/resources/', headers={'X-Auth': tok})
    with urllib.request.urlopen(res_req, context=ctx, timeout=5) as r:
        data = json.loads(r.read().decode('utf-8'))
        for it in sorted(data['items'], key=lambda x: x['name']):
            sys.stdout.buffer.write(('  📁 ' + it['name'] + '\n').encode('utf-8'))
except Exception as e:
    print("FB ERR:", e)

# 2. Check Native WebDAV PROPFIND
print("\n=== 2. NATIVE WEBDAV CHECK ===")
try:
    dav_req = urllib.request.Request('https://178.140.8.56:34503/webdav/')
    dav_req.add_header('Authorization', 'Basic ' + base64.b64encode(b'admin:12345678').decode())
    dav_req.add_header('Depth', '1')
    dav_req.get_method = lambda: 'PROPFIND'
    with urllib.request.urlopen(dav_req, context=ctx, timeout=5) as r:
        import re, urllib.parse
        xml = r.read().decode('utf-8', errors='replace')
        hrefs = re.findall(r'<[^>]*href[^>]*>(.*?)</[^>]*href[^>]*>', xml)
        for h in hrefs:
            sys.stdout.buffer.write(('  -> ' + urllib.parse.unquote(h) + '\n').encode('utf-8'))
except Exception as e:
    print("DAV ERR:", e)

# 3. Check ownCloud WebDAV
print("\n=== 3. OWNCLOUD CHECK ===")
try:
    oc_req = urllib.request.Request('https://178.140.8.56:34501/pkg/ownCloud/remote.php/webdav/')
    oc_req.add_header('Authorization', 'Basic ' + base64.b64encode(b'admin:12345678').decode())
    oc_req.add_header('Depth', '1')
    oc_req.get_method = lambda: 'PROPFIND'
    with urllib.request.urlopen(oc_req, context=ctx, timeout=5) as r:
        import re, urllib.parse
        xml = r.read().decode('utf-8', errors='replace')
        hrefs = re.findall(r'<d:href>(.*?)</d:href>', xml)
        for h in hrefs:
            name = urllib.parse.unquote(h).rstrip('/').split('/')[-1]
            if name in ['Личное', 'Стоматология', 'Обучение', 'Рабочая флэшка', 'Работа', 'Медиа', 'Бэкап']:
                sys.stdout.buffer.write(('  -> ' + name + '\n').encode('utf-8'))
except Exception as e:
    print("OC ERR:", e)
