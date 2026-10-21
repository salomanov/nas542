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
echo "=== FIND PHP ==="
find / -name "php*" -type f 2>/dev/null | grep -E "bin|sbin"

echo "=== FIND ARIA2 CONF ==="
find / -name "*aria2*" 2>/dev/null | grep -E "conf|service|init"

echo "=== FIND TRANSMISSION SETTINGS ==="
find / -name "settings.json" 2>/dev/null

echo "=== LIST /i-data/dadf1c38/????? ==="
find /i-data/dadf1c38/ -mindepth 1 -maxdepth 2 ! -path "*/Media*" ! -path "*/.system*" ! -path "*/.media*" ! -path "*/lost+found*" ! -path "*/disk3*" ! -name "aquota.user"
'''
s.sendall(cmd.encode('utf-8'))
time.sleep(4)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
