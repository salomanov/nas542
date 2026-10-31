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
echo "=== DOWNLOADS CHECK ==="
ls -la /i-data/45f1aca1/Apps/aria2/downloads 2>/dev/null || true
ls -la /i-data/45f1aca1/Apps/transmission/downloads 2>/dev/null || true

echo "=== CHECK DISK 3 LEFTOVER ==="
find /i-data/dadf1c38/ -maxdepth 3 ! -path "*/Media*" ! -path "*/.system*" ! -path "*/.media*" ! -path "*/lost+found*" ! -path "*/disk3*"

echo "=== TEST OWNCLOUD SCAN ==="
export LD_LIBRARY_PATH=/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/lib:/usr/local/apache/lib:/usr/local/zy-pkgs/lib:$LD_LIBRARY_PATH
/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/php/bin/php /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/console.php files:scan --all
'''
s.sendall(cmd.encode('utf-8'))
time.sleep(5)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
