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
/opt/etc/init.d/S81aria2 restart
echo "=== DISK 3 CLEAN STATUS ==="
ls -la /i-data/dadf1c38/
echo "=== MEDIA DOWNLOADS CONTENT ==="
ls -la /i-data/dadf1c38/Media/Downloads/
echo "=== DF -H ==="
df -h | grep "/i-data/"
'''
s.sendall(cmd.encode('utf-8'))
time.sleep(3)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
