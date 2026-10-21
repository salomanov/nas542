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
with open('/etc/samba/smb.conf', 'r') as f:
    orig = f.read()

# Add test Russian share
test_block = u"""
[Тест_Личное]
\tpath = /i-data/45f1aca1/Personal
\tfollow symlinks = yes
\tbrowseable = yes
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes
""".encode('utf-8')

with open('/etc/samba/smb.conf', 'a') as f:
    f.write(test_block)

import os
os.system("killall -HUP smbd")
'''.encode('utf-8')

hex_data = binascii.hexlify(remote_code).decode('ascii')
runner_cmd = 'python -c "import binascii; open(\'/tmp/test_smb.py\', \'wb\').write(binascii.unhexlify(\'%s\'))" && python /tmp/test_smb.py\n' % hex_data
s.sendall(runner_cmd.encode('ascii'))
time.sleep(2)
out = s.recv(4096).decode('utf-8', errors='ignore')
print("RELOAD_OUT:", out)

s.close()
