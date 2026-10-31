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
cat << 'EOF' > /tmp/check_oc_apps.py
import sqlite3
con = sqlite3.connect('/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/data/owncloud.db')
cur = con.cursor()
print "ENABLED APPS:"
for r in cur.execute("SELECT appid FROM oc_appconfig WHERE configkey='enabled' AND configvalue='yes'").fetchall():
    print "  -", r[0]

print "FILES_SHARING KEYS:"
for r in cur.execute("SELECT * FROM oc_appconfig WHERE appid='files_sharing'").fetchall():
    print "  ", r
EOF
python /tmp/check_oc_apps.py
'''
s.sendall(cmd.encode('ascii'))
time.sleep(2)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
