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

s.sendall(b'sqlite3 /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/data/owncloud.db "SELECT * FROM oc_appconfig WHERE appid=\'files_external\';"\n')
time.sleep(1.5)
s.sendall(b'sqlite3 /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/data/owncloud.db "SELECT * FROM oc_appconfig WHERE configkey=\'installed_apps\';"\n')
time.sleep(1.5)
out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
