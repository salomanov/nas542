# -*- coding: utf-8 -*-
import socket
import time
import binascii

remote_python = u'''# -*- coding: utf-8 -*-
import os

storage = "/i-data/45f1aca1/Storage"
# remove old symlinks
os.system("rm -f " + storage + "/*")

d1 = u"/i-data/45f1aca1/Личное".encode('utf-8')
d2 = u"/i-data/8c0fa088/Работа".encode('utf-8')
d3 = u"/i-data/dadf1c38/Медиа".encode('utf-8')
d4 = u"/i-data/d4877b70/Бэкап".encode('utf-8')

s1 = storage + u"/Личное".encode('utf-8')
s2 = storage + u"/Работа".encode('utf-8')
s3 = storage + u"/Медиа".encode('utf-8')
s4 = storage + u"/Бэкап".encode('utf-8')

os.system("mkdir -p " + s1)
os.system("mkdir -p " + s2)
os.system("mkdir -p " + s3)
os.system("mkdir -p " + s4)

os.system("mount --bind " + d1 + " " + s1)
os.system("mount --bind " + d2 + " " + s2)
os.system("mount --bind " + d3 + " " + s3)
os.system("mount --bind " + d4 + " " + s4)

print("BIND_MOUNTS_CREATED")
'''.encode('utf-8')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(15)
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

hex_data = binascii.hexlify(remote_python).decode('ascii')
chunks = [hex_data[i:i+64] for i in range(0, len(hex_data), 64)]

s.sendall(b"> /tmp/bind.hex\n")
time.sleep(0.5)

for ch in chunks:
    s.sendall(('echo "%s" >> /tmp/bind.hex\n' % ch).encode('ascii'))
    time.sleep(0.04)

time.sleep(0.5)
s.sendall(b"python -c \"import binascii; open('/tmp/bind.py', 'wb').write(binascii.unhexlify(open('/tmp/bind.hex').read().replace('\\n','')))\" && python /tmp/bind.py\n")

time.sleep(2)
s.sendall(b"python /tmp/test_propfind.py\n")
time.sleep(2)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
