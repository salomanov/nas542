import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
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

cmd = '''
cat /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/appinfo/app.php
echo "=== ROUTES ==="
cat /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/appinfo/routes.php 2>/dev/null || true
'''
s.sendall(cmd.encode('ascii'))
time.sleep(2)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
