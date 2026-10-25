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

cmd1 = b"python -c \"import binascii; open('/tmp/do_patch.py', 'wb').write(binascii.unhexlify(open('/tmp/do_patch.hex').read().strip()))\"\n"
s.sendall(cmd1)
print("CMD1:", ru(b'# ').decode())

cmd2 = b"python /tmp/do_patch.py\n"
s.sendall(cmd2)
print("CMD2:", ru(b'# ').decode())

s.close()
