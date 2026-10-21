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

commands = [
    b'grep -rn "OC_OCS_Cloud" /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/ 2>/dev/null\n'
]

for cmd in commands:
    s.sendall(cmd)
    time.sleep(2)
    try:
        out = s.recv(4096).decode('ascii', errors='ignore')
        print(">>> CMD:", cmd.decode().strip())
        print(out)
    except Exception as e:
        print("Recv err:", e)

s.close()
