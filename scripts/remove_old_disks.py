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

cmd = '''
python -c "
# Clean smb.conf
with open('/etc/samba/smb.conf', 'r') as f:
    lines = f.readlines()
new_lines = []
skip = False
for l in lines:
    sl = l.strip()
    if sl in ['[disk1]', '[disk2]', '[disk3]', '[disk4]']:
        skip = True
        continue
    if skip and sl.startswith('['):
        skip = False
    if not skip:
        new_lines.append(l)
with open('/etc/samba/smb.conf', 'w') as f:
    f.writelines(new_lines)

# Clean httpd_dav_auth.conf
with open('/etc/service_conf/httpd_dav_auth.conf', 'r') as f:
    dlines = f.readlines()
new_dlines = []
dskip = False
for l in dlines:
    if any(k in l for k in ['[ disk1 ]', '[ disk2 ]', '[ disk3 ]', '[ disk4 ]', '[ 1 ]']):
        dskip = True
        continue
    if dskip and l.startswith('####### ['):
        dskip = False
    if not dskip:
        new_dlines.append(l)
with open('/etc/service_conf/httpd_dav_auth.conf', 'w') as f:
    f.writelines(new_dlines)
"
killall -HUP smbd
/etc/init.d/davhttpd.sh reload

# Remove empty disk1..disk4 folders if empty
rmdir /i-data/45f1aca1/disk1 2>/dev/null || true
rmdir /i-data/8c0fa088/disk2 2>/dev/null || true
rmdir /i-data/dadf1c38/disk3 2>/dev/null || true
rmdir /i-data/d4877b70/disk4 2>/dev/null || true

echo "OLD_DISKS_REMOVED"
'''
s.sendall(cmd.encode('ascii'))
time.sleep(3)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
