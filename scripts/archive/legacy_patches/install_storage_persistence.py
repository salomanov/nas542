import socket
import time
import binascii

remote_script = u'''#!/bin/sh
cat << 'EOF' > /i-data/45f1aca1/Apps/ensure_storage_mounts.sh
#!/bin/sh
storage="/i-data/45f1aca1/Storage"
mkdir -p "$storage/Личное" "$storage/Работа" "$storage/Медиа" "$storage/Бэкап"

grep -q " $storage/Личное " /proc/mounts || mount --bind /i-data/45f1aca1/Личное "$storage/Личное"
grep -q " $storage/Работа " /proc/mounts || mount --bind /i-data/8c0fa088/Работа "$storage/Работа"
grep -q " $storage/Медиа " /proc/mounts || mount --bind /i-data/dadf1c38/Медиа "$storage/Медиа"
grep -q " $storage/Бэкап " /proc/mounts || mount --bind /i-data/d4877b70/Бэкап "$storage/Бэкап"

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
EOF

chmod +x /i-data/45f1aca1/Apps/ensure_storage_mounts.sh

# Link to Entware init.d
cat << 'INEOF' > /opt/etc/init.d/S05storage-mounts
#!/bin/sh
case "$1" in
    start)
        /i-data/45f1aca1/Apps/ensure_storage_mounts.sh
        ;;
    stop)
        ;;
    *)
        /i-data/45f1aca1/Apps/ensure_storage_mounts.sh
        ;;
esac
INEOF
chmod +x /opt/etc/init.d/S05storage-mounts

echo "PERSISTENCE_INSTALLED"
'''

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

hex_data = binascii.hexlify(remote_script.encode('utf-8')).decode('ascii')
chunks = [hex_data[i:i+64] for i in range(0, len(hex_data), 64)]

s.sendall(b"> /tmp/p_storage.hex\n")
time.sleep(0.5)

for ch in chunks:
    s.sendall(('echo "%s" >> /tmp/p_storage.hex\n' % ch).encode('ascii'))
    time.sleep(0.04)

time.sleep(0.5)
s.sendall(b"python -c \"import binascii; open('/tmp/p_storage.sh', 'wb').write(binascii.unhexlify(open('/tmp/p_storage.hex').read().replace('\\n','')))\" && chmod +x /tmp/p_storage.sh && /tmp/p_storage.sh\n")

time.sleep(2)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
