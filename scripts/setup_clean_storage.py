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

remote_script = u'''# -*- coding: utf-8 -*-
import os

storage = "/i-data/45f1aca1/Storage"
os.system("mkdir -p " + storage)

# Create links without prefixes in Storage
os.system("ln -sfn /i-data/45f1aca1/Личное " + storage + "/Личное")
os.system("ln -sfn /i-data/8c0fa088/Работа " + storage + "/Работа")
os.system("ln -sfn /i-data/dadf1c38/Медиа " + storage + "/Медиа")
os.system("ln -sfn /i-data/d4877b70/Бэкап " + storage + "/Бэкап")

# Remove 1_, 2_, 3_, 4_ links from /i-data/45f1aca1/
os.system("rm -f /i-data/45f1aca1/1_* /i-data/45f1aca1/2_* /i-data/45f1aca1/3_* /i-data/45f1aca1/4_*")

# Update FileBrowser root in /opt/etc/filebrowser/filebrowser.conf
with open('/opt/etc/filebrowser/filebrowser.conf', 'r') as f:
    conf = f.read()

conf = conf.replace('ROOT="-r /i-data/45f1aca1"', 'ROOT="-r /i-data/45f1aca1/Storage"')
with open('/opt/etc/filebrowser/filebrowser.conf', 'w') as f:
    f.write(conf)

os.system("/opt/etc/init.d/S99filebrowser restart")
print("STORAGE_ROOT_CONFIGURED")
'''.encode('utf-8')

hex_data = binascii.hexlify(remote_script).decode('ascii')
chunks = [hex_data[i:i+64] for i in range(0, len(hex_data), 64)]

s.sendall(b"> /tmp/fb_clean.hex\n")
time.sleep(0.5)

for ch in chunks:
    s.sendall(('echo "%s" >> /tmp/fb_clean.hex\n' % ch).encode('ascii'))
    time.sleep(0.04)

time.sleep(0.5)
s.sendall(b"python -c \"import binascii; open('/tmp/fb_clean.py', 'wb').write(binascii.unhexlify(open('/tmp/fb_clean.hex').read().replace('\\n','')))\" && python /tmp/fb_clean.py\n")

time.sleep(3)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
