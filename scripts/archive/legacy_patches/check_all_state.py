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

cmd = b'''
echo "=== SAMBA SECTIONS ==="
grep -E '^\[' /etc/samba/smb.conf
echo "=== DISK 1 ROOT ==="
ls -la /i-data/45f1aca1/
echo "=== DISK 3 LEFTOVER ==="
find /i-data/dadf1c38/ -maxdepth 2
'''
s.sendall(cmd)
time.sleep(3)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
