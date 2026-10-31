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

clean_script = '''#!/bin/sh
set -e

# Target directories
mkdir -p /i-data/45f1aca1/Personal/Documents
mkdir -p /i-data/45f1aca1/Personal/Photos
mkdir -p /i-data/45f1aca1/Personal/Videos

mkdir -p /i-data/8c0fa088/Work/Projects
mkdir -p /i-data/8c0fa088/Work/Documents
mkdir -p /i-data/8c0fa088/Work/Shared

mkdir -p /i-data/dadf1c38/Media/Movies
mkdir -p /i-data/dadf1c38/Media/Music
mkdir -p /i-data/dadf1c38/Media/Books
mkdir -p /i-data/dadf1c38/Media/Downloads

mkdir -p /i-data/d4877b70/Backup/Computers
mkdir -p /i-data/d4877b70/Backup/NAS_Snapshots

# Safely locate and move Green Book to /i-data/dadf1c38/Media/Movies/
find /i-data/8c0fa088/ -name "*Green Book*" ! -name "._*" -exec mv -f {} /i-data/dadf1c38/Media/Movies/ \; 2>/dev/null || true
find /i-data/dadf1c38/ -maxdepth 3 -name "*Green Book*" ! -path "*/Media/Movies/*" -exec mv -f {} /i-data/dadf1c38/Media/Movies/ \; 2>/dev/null || true

# Move videos to Personal/Videos
find /i-data/8c0fa088/ -name "VID_*" -exec mv -f {} /i-data/45f1aca1/Personal/Videos/ \; 2>/dev/null || true
find /i-data/d4877b70/disk4/ -name "VID_*" -exec mv -f {} /i-data/45f1aca1/Personal/Videos/ \; 2>/dev/null || true

# Remove unwanted apks and old folder 1
rm -rf /i-data/8c0fa088/1
rm -rf /i-data/d4877b70/.PKG

# Clean macOS junk across all 4 disks
find /i-data/ -name ".DS_Store" -delete 2>/dev/null || true
find /i-data/ -name "._*" -delete 2>/dev/null || true

# Set permissions
chown -R admin:everyone /i-data/45f1aca1/Personal /i-data/8c0fa088/Work /i-data/dadf1c38/Media /i-data/d4877b70/Backup
chmod -R 777 /i-data/45f1aca1/Personal /i-data/8c0fa088/Work /i-data/dadf1c38/Media /i-data/d4877b70/Backup

# Create symlinks in FileBrowser root (/i-data/45f1aca1)
ln -sfn /i-data/45f1aca1/Personal /i-data/45f1aca1/1_Personal
ln -sfn /i-data/8c0fa088/Work /i-data/45f1aca1/2_Work
ln -sfn /i-data/dadf1c38/Media /i-data/45f1aca1/3_Media
ln -sfn /i-data/d4877b70/Backup /i-data/45f1aca1/4_Backup

echo "STRUCTURE_READY"
'''

s.sendall(b"cat << 'EOF' > /tmp/do_clean_link.sh\n" + clean_script.encode('ascii') + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /tmp/do_clean_link.sh && /tmp/do_clean_link.sh\n")
time.sleep(5)
out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
