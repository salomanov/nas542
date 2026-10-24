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
tail -n 60 /etc/samba/smb.conf
echo "=== LOG SMBD ==="
ls -la /var/log/samba* /var/log/*smb* 2>/dev/null || true
tail -n 30 /var/log/samba/log.smbd 2>/dev/null || tail -n 30 /var/log/log.smbd 2>/dev/null || true
'''
s.sendall(cmd.encode('ascii'))
time.sleep(3)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
