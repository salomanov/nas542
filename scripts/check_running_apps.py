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
echo "=== TESTING LD_LIBRARY_PATH FOR PHP ==="
find /i-data/45f1aca1/.PKG/ -name "libmcrypt*" 2>/dev/null
export LD_LIBRARY_PATH=/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/lib:/usr/local/apache/lib:/usr/local/zy-pkgs/lib:$LD_LIBRARY_PATH
/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/php/bin/php -v

echo "=== CHECKING ARIA2 CONF ==="
grep -i "dir" /opt/etc/aria2.conf

echo "=== CHECKING TRANSMISSION SETTINGS ==="
grep -i "dir" /opt/etc/transmission/settings.json
'''
s.sendall(cmd.encode('utf-8'))
time.sleep(3)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
