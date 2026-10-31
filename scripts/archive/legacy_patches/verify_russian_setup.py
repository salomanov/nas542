# -*- coding: utf-8 -*-
import urllib.request
import json
import ssl
import binascii
import socket
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Check FileBrowser with password 12345678
fb_url = "https://178.140.8.56:34501/apps/fb/api/login"
req = urllib.request.Request(
    fb_url,
    data=json.dumps({"username": "admin", "password": "12345678"}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        token = resp.read().decode('utf-8')
        print(">>> FILEBROWSER AUTH SUCCESSFUL! TOKEN RECEIVED.")
        
        # Get root listing
        res_req = urllib.request.Request(
            "https://178.140.8.56:34501/apps/fb/api/resources/",
            headers={"X-Auth": token}
        )
        with urllib.request.urlopen(res_req, context=ctx, timeout=10) as res_resp:
            data = json.loads(res_resp.read().decode('utf-8'))
            items = data.get('items', [])
            print(">>> FILEBROWSER ROOT LISTING:")
            for item in sorted(items, key=lambda x: x['name']):
                if item['name'].startswith(('1_', '2_', '3_', '4_')):
                    print("   [DIR] %s" % item['name'])
                    
        # Check inside 3_Медиа
        media_req = urllib.request.Request(
            "https://178.140.8.56:34501/apps/fb/api/resources/3_%D0%9C%D0%B5%D0%B4%D0%B8%D0%B0",
            headers={"X-Auth": token}
        )
        with urllib.request.urlopen(media_req, context=ctx, timeout=10) as media_resp:
            media_data = json.loads(media_resp.read().decode('utf-8'))
            print(">>> INSIDE 3_Медиа:")
            for m in media_data.get('items', []):
                print("   - %s (%s)" % (m['name'], "DIR" if m['isDir'] else "FILE"))
except Exception as e:
    print("FILEBROWSER ERROR:", e)

# 2. Check smb.conf hex content
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(10)
s.connect(('178.140.8.56', 34523))
time.sleep(1)
s.recv(1024)
s.sendall(b'admin\n')
time.sleep(1)
s.recv(1024)
s.sendall(b'12345678\n')
time.sleep(1)
s.recv(1024)
s.sendall(b'/bin/busybox su\n')
time.sleep(1)
s.sendall(b'12345678\n')
time.sleep(1)
s.recv(1024)

s.sendall(b"python -c \"import binascii; print binascii.hexlify(open('/etc/samba/smb.conf').read()[-800:])\"\n")
time.sleep(2)
out = s.recv(4096).decode('ascii', errors='ignore')
for line in out.splitlines():
    line = line.strip()
    if len(line) > 100:
        decoded = binascii.unhexlify(line).decode('utf-8', errors='replace')
        print(">>> SAMBA CONFIG DECODED (UTF-8):")
        print(decoded)
s.close()
