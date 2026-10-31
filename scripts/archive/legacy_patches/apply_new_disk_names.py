# -*- coding: utf-8 -*-
import socket
import time
import binascii

remote_python_script = r'''# -*- coding: utf-8 -*-
import os, sys

storage = "/i-data/45f1aca1/Storage"

# 1. Unmount existing bind mounts in Storage
for item in [u"Личное", u"Работа", u"Медиа", u"Бэкап", u"Стоматология", u"Обучение", u"Рабочая флэшка"]:
    mp = os.path.join(storage, item.encode('utf-8'))
    os.system("umount '" + mp + "' 2>/dev/null || true")

# 2. Disk 2: Rename Работа -> Стоматология
d2_old = u"/i-data/8c0fa088/Работа".encode('utf-8')
d2_new = u"/i-data/8c0fa088/Стоматология".encode('utf-8')
if os.path.exists(d2_old):
    os.system("mv '" + d2_old + "' '" + d2_new + "'")
else:
    os.system("mkdir -p '" + d2_new + "'")
os.system("ln -sfn '" + d2_new + "' /i-data/8c0fa088/Work")

# 3. Disk 3: Rename Медиа -> Обучение
d3_old = u"/i-data/dadf1c38/Медиа".encode('utf-8')
d3_new = u"/i-data/dadf1c38/Обучение".encode('utf-8')
if os.path.exists(d3_old):
    os.system("mv '" + d3_old + "' '" + d3_new + "'")
else:
    os.system("mkdir -p '" + d3_new + "'")
os.system("ln -sfn '" + d3_new + "' /i-data/dadf1c38/Media")
os.system("ln -sfn '" + d3_new + "/Загрузки' /i-data/dadf1c38/Media/Downloads")
os.system("ln -sfn '" + d3_new + "/Загрузки' /i-data/45f1aca1/Apps/aria2/downloads")
os.system("ln -sfn '" + d3_new + "/Загрузки' /i-data/45f1aca1/Apps/transmission/downloads")

# 4. Disk 4: Rename Бэкап -> Рабочая флэшка
d4_old = u"/i-data/d4877b70/Бэкап".encode('utf-8')
d4_new = u"/i-data/d4877b70/Рабочая флэшка".encode('utf-8')
if os.path.exists(d4_old):
    os.system("mv '" + d4_old + "' '" + d4_new + "'")
else:
    os.system("mkdir -p '" + d4_new + "'")
os.system("ln -sfn '" + d4_new + "' /i-data/d4877b70/Backup")

# Disk 1: Личное remains
d1 = u"/i-data/45f1aca1/Личное".encode('utf-8')

# Ensure permissions
for p in [d1, d2_new, d3_new, d4_new]:
    os.system("chmod -R 777 '" + p + "'")
    os.system("chown -R admin:everyone '" + p + "'")

# 5. Clean up Storage mountpoints and recreate
os.system("rm -rf " + storage + "/*")

s1 = os.path.join(storage, u"Личное".encode('utf-8'))
s2 = os.path.join(storage, u"Стоматология".encode('utf-8'))
s3 = os.path.join(storage, u"Обучение".encode('utf-8'))
s4 = os.path.join(storage, u"Рабочая флэшка".encode('utf-8'))

for s in [s1, s2, s3, s4]:
    os.system("mkdir -p '" + s + "'")

os.system("mount --bind '" + d1 + "' '" + s1 + "'")
os.system("mount --bind '" + d2_new + "' '" + s2 + "'")
os.system("mount --bind '" + d3_new + "' '" + s3 + "'")
os.system("mount --bind '" + d4_new + "' '" + s4 + "'")

# 6. Update ownCloud symlinks
oc_dir = "/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/data/admin/files"
for old_link in [u"Работа", u"Медиа", u"Бэкап", u"Work", u"Media", u"Backup"]:
    os.system("rm -f '" + os.path.join(oc_dir, old_link.encode('utf-8')) + "'")

os.system("ln -sfn '" + d1 + "' '" + os.path.join(oc_dir, u"Личное".encode('utf-8')) + "'")
os.system("ln -sfn '" + d2_new + "' '" + os.path.join(oc_dir, u"Стоматология".encode('utf-8')) + "'")
os.system("ln -sfn '" + d3_new + "' '" + os.path.join(oc_dir, u"Обучение".encode('utf-8')) + "'")
os.system("ln -sfn '" + d4_new + "' '" + os.path.join(oc_dir, u"Рабочая флэшка".encode('utf-8')) + "'")

# 7. Update ensure_storage_mounts.sh persistence script
script_sh = r"""#!/bin/sh
storage="/i-data/45f1aca1/Storage"
mkdir -p "$storage/Личное" "$storage/Стоматология" "$storage/Обучение" "$storage/Рабочая флэшка"

grep -q " $storage/Личное " /proc/mounts || mount --bind /i-data/45f1aca1/Личное "$storage/Личное"
grep -q " $storage/Стоматология " /proc/mounts || mount --bind /i-data/8c0fa088/Стоматология "$storage/Стоматология"
grep -q " $storage/Обучение " /proc/mounts || mount --bind /i-data/dadf1c38/Обучение "$storage/Обучение"
grep -q " $storage/Рабочая флэшка " /proc/mounts || mount --bind "/i-data/d4877b70/Рабочая флэшка" "$storage/Рабочая флэшка"

dav_conf="/etc/service_conf/httpd_dav_auth.conf"
if [ -f "$dav_conf" ] && ! grep -q 'Alias "/webdav" "/i-data/45f1aca1/Storage"' "$dav_conf"; then
    cat << 'DAVEOF' >> "$dav_conf"

####### [ Storage - Unified 4 Disks WebDAV ] #########
Alias "/webdav" "/i-data/45f1aca1/Storage"

<Directory "/i-data/45f1aca1/Storage">
        Options FollowSymLinks
        AllowOverride All
        Order Allow,Deny
        Allow from all
</Directory>

<Location "/webdav">
        IndexOptions Charset=UTF-8
        Dav On
        DavMinTimeout 600
        DavDepthInfinity on
        AuthType Basic
        AuthName "DAV-Storage"
        AuthBasicProvider cache
        AuthnCacheProvider external
        AuthnCacheTimeout 10
        AuthExternal pwauth
        AuthzUnixgroup on
        <limit GET HEAD OPTIONS REPORT PROPFIND>
                require user "admin"
        </limit>
        <LimitExcept get head options>
                require user "admin"
        </LimitExcept>
</Location>
DAVEOF
    /etc/init.d/davhttpd.sh reload
fi
"""

with open('/i-data/45f1aca1/Apps/ensure_storage_mounts.sh', 'w') as f:
    f.write(script_sh)

os.system("chmod +x /i-data/45f1aca1/Apps/ensure_storage_mounts.sh")

# 8. Reload / restart services
os.system("/opt/etc/init.d/S99filebrowser restart")
os.system("/etc/init.d/davhttpd.sh reload")
os.system("killall -HUP smbd")

# 9. Rescan ownCloud in background
scan_cmd = "export LD_LIBRARY_PATH=/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/lib:/usr/local/apache/lib:/usr/local/zy-pkgs/lib:$LD_LIBRARY_PATH && /i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/php/bin/php /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/console.php files:scan admin >/dev/null 2>&1 &"
os.system(scan_cmd)

print("RENAME_TO_CUSTOM_NAMES_COMPLETED")
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
chunks = [hex_data[i:i+64] for i in range(0, len(hex_data), 64)]

print("Uploading %d chunks..." % len(chunks))
s.sendall(b"> /tmp/rename_disks.hex\n")
time.sleep(0.5)

for ch in chunks:
    s.sendall(('echo "%s" >> /tmp/rename_disks.hex\n' % ch).encode('ascii'))
    time.sleep(0.04)

time.sleep(0.5)
s.sendall(b"python -c \"import binascii; open('/tmp/rename_disks.py', 'wb').write(binascii.unhexlify(open('/tmp/rename_disks.hex').read().replace('\\n','')))\" && python /tmp/rename_disks.py\n")

time.sleep(6)
out = s.recv(8192).decode('utf-8', errors='ignore')
print(out)
s.close()
