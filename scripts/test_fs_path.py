import socket, sys

s = socket.socket()
s.connect(('178.140.8.56', 34523))
def ru(p):
    b = b''
    while p not in b:
        c = s.recv(1024)
        if not c: break
        b += c
    return b

ru(b'login: ')
s.sendall(b'admin\n')
ru(b'Password: ')
s.sendall(b'12345678\n')
ru(b'$ ')
s.sendall(b'/bin/busybox su\n')
ru(b'Password: ')
s.sendall(b'12345678\n')
ru(b'# ')

s.sendall(b"sed -n '10,35p' /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/remote.php\n")
raw = ru(b'# ')
sys.stdout.buffer.write(raw)
s.close()
