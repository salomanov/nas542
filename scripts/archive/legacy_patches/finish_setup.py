import socket
import time

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

script = '''#!/bin/sh
set -e

# 1. Clean corrupted directory on Disk 3
# Find and remove any directory in dadf1c38 that is NOT Media, .system, .media, lost+found, disk3
for dir in /i-data/dadf1c38/*; do
    case "$dir" in
        */Media|*/disk3|*/lost+found|*/aquota.user)
            ;;
        *)
            echo "Removing leftover: $dir"
            rm -rf "$dir"
            ;;
    esac
done

# 2. Move existing downloads to /i-data/dadf1c38/Media/Downloads/
mv -f /i-data/45f1aca1/Apps/aria2/downloads/* /i-data/dadf1c38/Media/Downloads/ 2>/dev/null || true
rm -rf /i-data/45f1aca1/Apps/aria2/downloads
ln -sfn /i-data/dadf1c38/Media/Downloads /i-data/45f1aca1/Apps/aria2/downloads

rm -rf /i-data/45f1aca1/Apps/transmission/downloads
ln -sfn /i-data/dadf1c38/Media/Downloads /i-data/45f1aca1/Apps/transmission/downloads

# 3. Update aria2.conf
sed -i 's|^dir=.*|dir=/i-data/dadf1c38/Media/Downloads|g' /opt/etc/aria2.conf

# 4. Update transmission settings.json (stop daemon first to prevent overwrite)
/opt/etc/init.d/S88transmission stop || true
sleep 1
sed -i 's|"download-dir": ".*"|"download-dir": "/i-data/dadf1c38/Media/Downloads"|g' /opt/etc/transmission/settings.json
/opt/etc/init.d/S88transmission start || true

# 5. Restart aria2
/opt/etc/init.d/S89aria2 restart 2>/dev/null || (/opt/etc/init.d/S*aria* restart 2>/dev/null || true)

# 6. Ensure permissions on Media/Downloads
chmod -R 777 /i-data/dadf1c38/Media/Downloads
chown -R admin:everyone /i-data/dadf1c38/Media/Downloads

echo "CLEANUP_AND_DOWNLOADS_CONFIGURED"
'''

s.sendall(b"cat << 'EOF' > /tmp/do_finish_setup.sh\n" + script.encode('ascii') + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /tmp/do_finish_setup.sh && /tmp/do_finish_setup.sh\n")
time.sleep(6)
out = s.recv(8192).decode('ascii', errors='ignore')
print(out)
s.close()
