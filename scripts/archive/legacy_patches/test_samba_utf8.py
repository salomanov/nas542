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

cmd = r'''
cat << 'EOF' > /tmp/test_smb.py
# -*- coding: utf-8 -*-
with open('/etc/samba/smb.conf', 'r', encoding='utf-8', errors='ignore') as f:
    orig = f.read()

test_share = """
[Личное]
\tpath = /i-data/45f1aca1/Personal
\tfollow symlinks = yes
\tbrowseable = yes
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes
"""
with open('/etc/samba/smb.conf', 'a', encoding='utf-8') as f:
    f.write(test_share)
EOF
python /tmp/test_smb.py
killall -HUP smbd
sleep 1
pidof smbd
'''
s.sendall(cmd.encode('utf-8'))
time.sleep(3)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)

# Clean test share
clean_cmd = r'''
cat << 'EOF' > /tmp/clean_smb.py
# -*- coding: utf-8 -*-
with open('/etc/samba/smb.conf', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
with open('/etc/samba/smb.conf', 'w', encoding='utf-8') as f:
    for line in lines:
        if '[Личное]' in line:
            break
        f.write(line)
EOF
python /tmp/clean_smb.py
killall -HUP smbd
'''
s.sendall(clean_cmd.encode('utf-8'))
time.sleep(2)
s.close()
