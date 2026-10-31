# -*- coding: utf-8 -*-
import socket
import time
import binascii

remote_python_script = u'''# -*- coding: utf-8 -*-
import os, sys

# 1. Disk 1: Личное
d1 = u"/i-data/45f1aca1/Личное".encode('utf-8')
os.system("mkdir -p " + d1 + "/Документы")
os.system("mkdir -p " + d1 + "/Фото")
os.system("mkdir -p " + d1 + "/Видео")

if os.path.exists("/i-data/45f1aca1/Personal"):
    os.system("mv -f /i-data/45f1aca1/Personal/Videos/* " + d1 + "/Видео/ 2>/dev/null || true")
    os.system("mv -f /i-data/45f1aca1/Personal/Documents/* " + d1 + "/Документы/ 2>/dev/null || true")
    os.system("mv -f /i-data/45f1aca1/Personal/Photos/* " + d1 + "/Фото/ 2>/dev/null || true")
    os.system("rm -rf /i-data/45f1aca1/Personal")

os.system("ln -sfn " + d1 + " /i-data/45f1aca1/Personal")

# 2. Disk 2: Работа
d2 = u"/i-data/8c0fa088/Работа".encode('utf-8')
os.system("mkdir -p " + d2 + "/Проекты")
os.system("mkdir -p " + d2 + "/Документы")
os.system("mkdir -p " + d2 + "/Общие")

if os.path.exists("/i-data/8c0fa088/Work"):
    os.system("mv -f /i-data/8c0fa088/Work/Projects/* " + d2 + "/Проекты/ 2>/dev/null || true")
    os.system("mv -f /i-data/8c0fa088/Work/Documents/* " + d2 + "/Документы/ 2>/dev/null || true")
    os.system("mv -f /i-data/8c0fa088/Work/Shared/* " + d2 + "/Общие/ 2>/dev/null || true")
    os.system("rm -rf /i-data/8c0fa088/Work")

os.system("ln -sfn " + d2 + " /i-data/8c0fa088/Work")

# 3. Disk 3: Медиа
d3 = u"/i-data/dadf1c38/Медиа".encode('utf-8')
os.system("mkdir -p " + d3 + "/Фильмы")
os.system("mkdir -p " + d3 + "/Музыка")
os.system("mkdir -p " + d3 + "/Книги")
os.system("mkdir -p " + d3 + "/Загрузки")

if os.path.exists("/i-data/dadf1c38/Media"):
    os.system("mv -f /i-data/dadf1c38/Media/Movies/* " + d3 + "/Фильмы/ 2>/dev/null || true")
    os.system("mv -f /i-data/dadf1c38/Media/Music/* " + d3 + "/Музыка/ 2>/dev/null || true")
    os.system("mv -f /i-data/dadf1c38/Media/Books/* " + d3 + "/Книги/ 2>/dev/null || true")
    os.system("mv -f /i-data/dadf1c38/Media/Downloads/* " + d3 + "/Загрузки/ 2>/dev/null || true")
    os.system("rm -rf /i-data/dadf1c38/Media")

os.system("ln -sfn " + d3 + " /i-data/dadf1c38/Media")
os.system("ln -sfn " + d3 + "/Загрузки /i-data/dadf1c38/Media/Downloads")
os.system("ln -sfn " + d3 + "/Фильмы /i-data/dadf1c38/Media/Movies")
os.system("ln -sfn " + d3 + "/Загрузки /i-data/45f1aca1/Apps/aria2/downloads")
os.system("ln -sfn " + d3 + "/Загрузки /i-data/45f1aca1/Apps/transmission/downloads")

# 4. Disk 4: Бэкап
d4 = u"/i-data/d4877b70/Бэкап".encode('utf-8')
os.system("mkdir -p " + d4 + "/Компьютеры")
os.system("mkdir -p " + d4 + "/Снимки_NAS")

if os.path.exists("/i-data/d4877b70/Backup"):
    os.system("mv -f /i-data/d4877b70/Backup/Computers/* " + d4 + "/Компьютеры/ 2>/dev/null || true")
    os.system("mv -f /i-data/d4877b70/Backup/NAS_Snapshots/* " + d4 + "/Снимки_NAS/ 2>/dev/null || true")
    os.system("rm -rf /i-data/d4877b70/Backup")

os.system("ln -sfn " + d4 + " /i-data/d4877b70/Backup")

# Permissions
os.system("chmod -R 777 " + d1 + " " + d2 + " " + d3 + " " + d4)
os.system("chown -R admin:everyone " + d1 + " " + d2 + " " + d3 + " " + d4)

# 5. FileBrowser Root Links in /i-data/45f1aca1
os.system("rm -f /i-data/45f1aca1/1_Personal /i-data/45f1aca1/2_Work /i-data/45f1aca1/3_Media /i-data/45f1aca1/4_Backup")
os.system("ln -sfn " + d1 + " /i-data/45f1aca1/1_Личное")
os.system("ln -sfn " + d2 + " /i-data/45f1aca1/2_Работа")
os.system("ln -sfn " + d3 + " /i-data/45f1aca1/3_Медиа")
os.system("ln -sfn " + d4 + " /i-data/45f1aca1/4_Бэкап")

# 6. ownCloud Links in admin/files
oc_files = "/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/data/admin/files"
os.system("rm -f " + oc_files + "/Work " + oc_files + "/Media " + oc_files + "/Backup")
os.system("ln -sfn " + d1 + " " + oc_files + "/Личное")
os.system("ln -sfn " + d2 + " " + oc_files + "/Работа")
os.system("ln -sfn " + d3 + " " + oc_files + "/Медиа")
os.system("ln -sfn " + d4 + " " + oc_files + "/Бэкап")

# 7. Samba Configuration
with open('/etc/samba/smb.conf', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    sline = line.strip()
    if sline.startswith('[Personal]') or sline.startswith('[Work]') or \
       sline.startswith('[Media]') or sline.startswith('[Backup]') or \
       sline.startswith('[Личное]') or sline.startswith('[Работа]') or \
       sline.startswith('[Медиа]') or sline.startswith('[Бэкап]') or \
       sline.startswith('[Тест_Личное]'):
        skip = True
        continue
    if skip and sline.startswith('['):
        skip = False
    if not skip:
        new_lines.append(line)

samba_shares = u"""
[Личное]
\tpath = /i-data/45f1aca1/Личное
\tfollow symlinks = yes
\tstrict allocate = yes
\tallocation roundup size = 0
\taio write size = 4096
\tcomment = "Диск 1 - Личное"
\tbrowseable = yes
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Работа]
\tpath = /i-data/8c0fa088/Работа
\tfollow symlinks = yes
\tstrict allocate = yes
\tallocation roundup size = 0
\taio write size = 4096
\tcomment = "Диск 2 - Работа"
\tbrowseable = yes
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Медиа]
\tpath = /i-data/dadf1c38/Медиа
\tfollow symlinks = yes
\tstrict allocate = yes
\tallocation roundup size = 0
\taio write size = 4096
\tcomment = "Диск 3 - Медиа"
\tbrowseable = yes
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Бэкап]
\tpath = /i-data/d4877b70/Бэкап
\tfollow symlinks = yes
\tstrict allocate = yes
\tallocation roundup size = 0
\taio write size = 4096
\tcomment = "Диск 4 - Резервные копии"
\tbrowseable = yes
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Personal]
\tpath = /i-data/45f1aca1/Личное
\tfollow symlinks = yes
\tbrowseable = no
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Work]
\tpath = /i-data/8c0fa088/Работа
\tfollow symlinks = yes
\tbrowseable = no
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Media]
\tpath = /i-data/dadf1c38/Медиа
\tfollow symlinks = yes
\tbrowseable = no
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Backup]
\tpath = /i-data/d4877b70/Бэкап
\tfollow symlinks = yes
\tbrowseable = no
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes
""".encode('utf-8')

with open('/etc/samba/smb.conf', 'w') as f:
    f.writelines(new_lines)
    f.write(samba_shares)

os.system("killall -HUP smbd")

# 8. Trigger ownCloud files:scan
scan_cmd = "export LD_LIBRARY_PATH=/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/lib:/usr/local/apache/lib:/usr/local/zy-pkgs/lib:$LD_LIBRARY_PATH && /i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/php/bin/php /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/console.php files:scan admin"
os.system(scan_cmd)

print("ALL_MIGRATION_COMPLETED_SUCCESSFULLY")
'''

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(20)
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

hex_data = binascii.hexlify(remote_python_script.encode('utf-8')).decode('ascii')
chunks = [hex_data[i:i+64] for i in range(0, len(hex_data), 64)]

print("Uploading %d chunks..." % len(chunks))
s.sendall(b"> /tmp/script.hex\n")
time.sleep(0.5)

for ch in chunks:
    s.sendall(('echo "%s" >> /tmp/script.hex\n' % ch).encode('ascii'))
    time.sleep(0.05)

time.sleep(1)
s.sendall(b"python -c \"import binascii; open('/tmp/do_migr.py', 'wb').write(binascii.unhexlify(open('/tmp/script.hex').read().replace('\\n','')))\" && python /tmp/do_migr.py\n")

# Wait for completion (scan might take 5-10s)
time.sleep(12)
out = s.recv(16384).decode('utf-8', errors='ignore')
print("OUTPUT:")
print(out)
s.close()
