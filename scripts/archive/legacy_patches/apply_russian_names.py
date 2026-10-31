# -*- coding: utf-8 -*-
import socket
import time
import binascii

remote_python_script = u'''# -*- coding: utf-8 -*-
import os, sys, shutil

def run(cmd):
    print("RUN:", cmd)
    os.system(cmd)

# 1. Disk 1: Личное
d1_personal = u"/i-data/45f1aca1/Личное".encode('utf-8')
os.system("mkdir -p " + d1_personal + "/Документы")
os.system("mkdir -p " + d1_personal + "/Фото")
os.system("mkdir -p " + d1_personal + "/Видео")

# Move any files from Personal to Личное
if os.path.exists("/i-data/45f1aca1/Personal"):
    os.system("mv -f /i-data/45f1aca1/Personal/Videos/* " + d1_personal + "/Видео/ 2>/dev/null || true")
    os.system("mv -f /i-data/45f1aca1/Personal/Documents/* " + d1_personal + "/Документы/ 2>/dev/null || true")
    os.system("mv -f /i-data/45f1aca1/Personal/Photos/* " + d1_personal + "/Фото/ 2>/dev/null || true")
    os.system("rm -rf /i-data/45f1aca1/Personal")

# Symlink Personal -> Личное
os.system("ln -sfn " + d1_personal + " /i-data/45f1aca1/Personal")

# 2. Disk 2: Работа
d2_work = u"/i-data/8c0fa088/Работа".encode('utf-8')
os.system("mkdir -p " + d2_work + "/Проекты")
os.system("mkdir -p " + d2_work + "/Документы")
os.system("mkdir -p " + d2_work + "/Общие")

if os.path.exists("/i-data/8c0fa088/Work"):
    os.system("mv -f /i-data/8c0fa088/Work/Projects/* " + d2_work + "/Проекты/ 2>/dev/null || true")
    os.system("mv -f /i-data/8c0fa088/Work/Documents/* " + d2_work + "/Документы/ 2>/dev/null || true")
    os.system("mv -f /i-data/8c0fa088/Work/Shared/* " + d2_work + "/Общие/ 2>/dev/null || true")
    os.system("rm -rf /i-data/8c0fa088/Work")

os.system("ln -sfn " + d2_work + " /i-data/8c0fa088/Work")

# 3. Disk 3: Медиа
d3_media = u"/i-data/dadf1c38/Медиа".encode('utf-8')
os.system("mkdir -p " + d3_media + "/Фильмы")
os.system("mkdir -p " + d3_media + "/Музыка")
os.system("mkdir -p " + d3_media + "/Книги")
os.system("mkdir -p " + d3_media + "/Загрузки")

if os.path.exists("/i-data/dadf1c38/Media"):
    os.system("mv -f /i-data/dadf1c38/Media/Movies/* " + d3_media + "/Фильмы/ 2>/dev/null || true")
    os.system("mv -f /i-data/dadf1c38/Media/Music/* " + d3_media + "/Музыка/ 2>/dev/null || true")
    os.system("mv -f /i-data/dadf1c38/Media/Books/* " + d3_media + "/Книги/ 2>/dev/null || true")
    os.system("mv -f /i-data/dadf1c38/Media/Downloads/* " + d3_media + "/Загрузки/ 2>/dev/null || true")
    os.system("rm -rf /i-data/dadf1c38/Media")

os.system("ln -sfn " + d3_media + " /i-data/dadf1c38/Media")
os.system("ln -sfn " + d3_media + "/Загрузки /i-data/dadf1c38/Media/Downloads")
os.system("ln -sfn " + d3_media + "/Фильмы /i-data/dadf1c38/Media/Movies")
os.system("ln -sfn " + d3_media + "/Загрузки /i-data/45f1aca1/Apps/aria2/downloads")
os.system("ln -sfn " + d3_media + "/Загрузки /i-data/45f1aca1/Apps/transmission/downloads")

# 4. Disk 4: Бэкап
d4_backup = u"/i-data/d4877b70/Бэкап".encode('utf-8')
os.system("mkdir -p " + d4_backup + "/Компьютеры")
os.system("mkdir -p " + d4_backup + "/Снимки_NAS")

if os.path.exists("/i-data/d4877b70/Backup"):
    os.system("mv -f /i-data/d4877b70/Backup/Computers/* " + d4_backup + "/Компьютеры/ 2>/dev/null || true")
    os.system("mv -f /i-data/d4877b70/Backup/NAS_Snapshots/* " + d4_backup + "/Снимки_NAS/ 2>/dev/null || true")
    os.system("rm -rf /i-data/d4877b70/Backup")

os.system("ln -sfn " + d4_backup + " /i-data/d4877b70/Backup")

# Permissions
os.system("chmod -R 777 " + d1_personal + " " + d2_work + " " + d3_media + " " + d4_backup)
os.system("chown -R admin:everyone " + d1_personal + " " + d2_work + " " + d3_media + " " + d4_backup)

# 5. FileBrowser Root Links in /i-data/45f1aca1
os.system("rm -f /i-data/45f1aca1/1_Personal /i-data/45f1aca1/2_Work /i-data/45f1aca1/3_Media /i-data/45f1aca1/4_Backup")
os.system("ln -sfn " + d1_personal + " /i-data/45f1aca1/1_Личное")
os.system("ln -sfn " + d2_work + " /i-data/45f1aca1/2_Работа")
os.system("ln -sfn " + d3_media + " /i-data/45f1aca1/3_Медиа")
os.system("ln -sfn " + d4_backup + " /i-data/45f1aca1/4_Бэкап")

# 6. ownCloud Links in admin/files
oc_files = "/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/data/admin/files"
os.system("rm -f " + oc_files + "/Work " + oc_files + "/Media " + oc_files + "/Backup")
os.system("ln -sfn " + d1_personal + " " + oc_files + "/Личное")
os.system("ln -sfn " + d2_work + " " + oc_files + "/Работа")
os.system("ln -sfn " + d3_media + " " + oc_files + "/Медиа")
os.system("ln -sfn " + d4_backup + " " + oc_files + "/Бэкап")

# 7. Samba Configuration
with open('/etc/samba/smb.conf', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.strip().startswith('[Personal]') or line.strip().startswith('[Work]') or \
       line.strip().startswith('[Media]') or line.strip().startswith('[Backup]') or \
       line.strip().startswith('[Личное]') or line.strip().startswith('[Работа]') or \
       line.strip().startswith('[Медиа]') or line.strip().startswith('[Бэкап]') or \
       line.strip().startswith('[Тест_Личное]'):
        skip = True
        continue
    if skip and line.strip().startswith('['):
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
\tpath = /i-data/45f1aca1/Personal
\tfollow symlinks = yes
\tbrowseable = no
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Work]
\tpath = /i-data/8c0fa088/Work
\tfollow symlinks = yes
\tbrowseable = no
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Media]
\tpath = /i-data/dadf1c38/Media
\tfollow symlinks = yes
\tbrowseable = no
\tvalid users = "admin" "pc-guest"
\tguest ok = yes
\twrite ok = yes

[Backup]
\tpath = /i-data/d4877b70/Backup
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
print("MIGRATION_OK")
'''

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(15)
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
runner_cmd = 'python -c "import binascii; open(\'/tmp/migrate_russian.py\', \'wb\').write(binascii.unhexlify(\'%s\'))" && python /tmp/migrate_russian.py\n' % hex_data
s.sendall(runner_cmd.encode('ascii'))
time.sleep(6)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
