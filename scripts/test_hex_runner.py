import socket
import time
import binascii

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

remote_code = u'''# -*- coding: utf-8 -*-
import os, sys

path = "/i-data/45f1aca1/test_utf8"
os.system("mkdir -p " + path)

test_dir = os.path.join(path, u"Личное".encode('utf-8'))
if not os.path.exists(test_dir):
    os.makedirs(test_dir)

items = os.listdir(path)
print("ITEMS_FOUND:", [f.decode('utf-8') for f in items])

# cleanup
os.system("rm -rf " + path)
'''

hex_data = binascii.hexlify(remote_code.encode('utf-8')).decode('ascii')

runner_cmd = 'python -c "import binascii; open(\'/tmp/test_hex.py\', \'wb\').write(binascii.unhexlify(\'%s\'))" && python /tmp/test_hex.py\n' % hex_data
s.sendall(runner_cmd.encode('ascii'))
time.sleep(3)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
