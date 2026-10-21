import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(10)
s.connect(('178.140.8.56', 34523))

def read_until(prompt, timeout=5):
    buf = b''
    start = time.time()
    while time.time() - start < timeout:
        try:
            chunk = s.recv(1024)
            if not chunk:
                break
            buf += chunk
            if prompt in buf:
                return buf
        except socket.timeout:
            break
    return buf

print(read_until(b'login: '))
s.sendall(b'admin\n')
print(read_until(b'Password: '))
s.sendall(b'12345678\n')
time.sleep(1)
print(s.recv(1024).decode('ascii', errors='ignore'))

# su
s.sendall(b'/bin/busybox su\n')
time.sleep(1)
s.sendall(b'12345678\n')
time.sleep(1)

commands = [
    b'ps | grep -E "ssh|dropbear"\n',
    b'netstat -tulpn | grep 22\n',
    b'ls -la /i-data/45f1aca1/.PKG/Dropbear/\n',
    b'/i-data/45f1aca1/.PKG/Dropbear/etc/init.d/Dropbear status\n'
]

for cmd in commands:
    s.sendall(cmd)
    time.sleep(1)
    try:
        out = s.recv(4096).decode('ascii', errors='ignore')
        print(">>> CMD:", cmd.decode().strip())
        print(out)
    except Exception as e:
        print("Recv err:", e)

s.close()
