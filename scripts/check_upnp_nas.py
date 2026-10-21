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
    b'ps | grep -E "upnp|router|nat"\n',
    b'cat /etc/service_conf/upnp.conf 2>/dev/null\n',
    b'cat /etc/upnp* 2>/dev/null\n',
    b'grep -rn "65535" /etc/ 2>/dev/null\n'
]

for cmd in commands:
    s.sendall(cmd)
    time.sleep(1.5)
    try:
        out = s.recv(4096).decode('ascii', errors='ignore')
        print(">>> CMD:", cmd.decode().strip())
        print(out)
    except Exception as e:
        print("Recv err:", e)

s.close()
