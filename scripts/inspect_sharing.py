import socket
import time

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

cmd = '''
echo "=== 1. CHECKING OWNCLOUD LOGS ==="
tail -n 40 /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/data/owncloud.log 2>/dev/null

echo "=== 2. CHECKING APACHE ACCESS LOGS ==="
tail -n 40 /var/log/httpd/oc_access.log 2>/dev/null || tail -n 40 /var/log/httpd/access_log 2>/dev/null || tail -n 40 /var/log/httpd2_access.log 2>/dev/null

echo "=== 3. CHECKING FILES_SHARING APP ==="
ls -la /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing 2>/dev/null
grep -i "share" /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/config/config.php
'''
s.sendall(cmd.encode('ascii'))
time.sleep(3)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
