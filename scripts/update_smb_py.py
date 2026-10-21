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

py_code = '''
with open("/etc/samba/smb.conf", "r") as f:
    text = f.read()

# remove section [1]
import re
text = re.sub(r'\\[1\\]\\n(?:\\t.*\\n)*', '', text)

new_shares = """
[Personal]
        path = /i-data/45f1aca1/Personal
        follow symlinks = yes
        strict allocate = yes
        allocation roundup size = 0
        aio write size = 4096
        comment = "Personal (Disk 1)"
        browseable = yes
        valid users = "admin" "pc-guest"
        guest ok = yes
        write ok = yes

[Work]
        path = /i-data/8c0fa088/Work
        follow symlinks = yes
        strict allocate = yes
        allocation roundup size = 0
        aio write size = 4096
        comment = "Work (Disk 2)"
        browseable = yes
        valid users = "admin" "pc-guest"
        guest ok = yes
        write ok = yes

[Media]
        path = /i-data/dadf1c38/Media
        follow symlinks = yes
        strict allocate = yes
        allocation roundup size = 0
        aio write size = 4096
        comment = "Media (Disk 3)"
        browseable = yes
        valid users = "admin" "pc-guest"
        guest ok = yes
        write ok = yes

[Backup]
        path = /i-data/d4877b70/Backup
        follow symlinks = yes
        strict allocate = yes
        allocation roundup size = 0
        aio write size = 4096
        comment = "Backup (Disk 4)"
        browseable = yes
        valid users = "admin" "pc-guest"
        guest ok = yes
        write ok = yes
"""

if "[Personal]" not in text:
    text += new_shares

with open("/etc/samba/smb.conf", "w") as f:
    f.write(text)

import os
os.system("killall -HUP smbd 2>/dev/null")
print("SAMBA_SUCCESS")
'''

s.sendall(b"python -c '" + py_code.strip().encode('ascii') + b"'\n")
time.sleep(2)
out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
