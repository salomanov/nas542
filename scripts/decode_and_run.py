import socket

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

s.sendall(b"python -c \"import binascii; open('/tmp/patch_dedup.py', 'wb').write(binascii.unhexlify(open('/tmp/patch_dedup.hex').read().strip()))\"\n")
print('DECODE:', ru(b'# ').decode())

s.sendall(b"python /tmp/patch_dedup.py\n")
print('RUN:', ru(b'# ').decode())

s.close()
