import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
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
cat << 'EOF' > /tmp/clean_smb.py
with open('/etc/samba/smb.conf', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for l in lines:
    sl = l.strip()
    if sl.startswith('[') and not sl.startswith(('[global]', '[printers]', '[admin]', '[music]', '[photo]', '[video]', '[Cloud]')):
        skip = True
        continue
    if skip and sl.startswith('['):
        if sl.startswith(('[global]', '[printers]', '[admin]', '[music]', '[photo]', '[video]', '[Cloud]')):
            skip = False
        else:
            continue
    if not skip:
        new_lines.append(l)

with open('/etc/samba/smb.conf', 'w') as f:
    f.writelines(new_lines)
EOF
python /tmp/clean_smb.py
killall -HUP smbd
echo "SMB_CLEANED_OK"
'''
s.sendall(cmd.encode('ascii'))
time.sleep(2)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
