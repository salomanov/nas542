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

bg_script = '''#!/bin/sh
# 1. Clean incomplete copy
rm -f "/i-data/dadf1c38/Media/Movies/Green Book (2018).mkv"
rm -rf "/i-data/dadf1c38/???"* 2>/dev/null || true

# 2. Move Green Book from disk 2 to disk 3
if [ -f "/i-data/8c0fa088/1/Green Book (2018).mkv" ]; then
    echo "Starting full move of Green Book..."
    cp -p "/i-data/8c0fa088/1/Green Book (2018).mkv" "/i-data/dadf1c38/Media/Movies/" && rm -f "/i-data/8c0fa088/1/Green Book (2018).mkv"
fi

# 3. Move videos to Personal/Videos
if [ -f "/i-data/8c0fa088/1/VID_20261004_215242.mp4" ]; then
    mv -f "/i-data/8c0fa088/1/VID_20261004_215242.mp4" "/i-data/45f1aca1/Personal/Videos/"
fi
if [ -f "/i-data/d4877b70/disk4/VID_20260812_094514_213.mp4" ]; then
    mv -f "/i-data/d4877b70/disk4/VID_20260812_094514_213.mp4" "/i-data/45f1aca1/Personal/Videos/"
fi

# 4. Clean up old folder 1 and apks
rm -rf "/i-data/8c0fa088/1"
rm -rf "/i-data/d4877b70/.PKG"
rm -f "/i-data/45f1aca1/test_link"

# 5. Create symlinks in FileBrowser root
ln -sfn /i-data/45f1aca1/Personal /i-data/45f1aca1/1_Personal
ln -sfn /i-data/8c0fa088/Work     /i-data/45f1aca1/2_Work
ln -sfn /i-data/dadf1c38/Media    /i-data/45f1aca1/3_Media
ln -sfn /i-data/d4877b70/Backup   /i-data/45f1aca1/4_Backup

# 6. Set full permissions
chown -R admin:everyone /i-data/45f1aca1/Personal /i-data/8c0fa088/Work /i-data/dadf1c38/Media /i-data/d4877b70/Backup
chmod -R 777 /i-data/45f1aca1/Personal /i-data/8c0fa088/Work /i-data/dadf1c38/Media /i-data/d4877b70/Backup

# 7. Clean macOS junk
find /i-data/ -name ".DS_Store" -delete 2>/dev/null || true
find /i-data/ -name "._*" -delete 2>/dev/null || true

echo "ALL_DONE" > /tmp/bg_move.status
'''

s.sendall(b"cat << 'EOF' > /tmp/bg_move.sh\n" + bg_script.encode('ascii') + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /tmp/bg_move.sh && nohup /tmp/bg_move.sh > /tmp/bg_move.log 2>&1 &\n")
time.sleep(2)
out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
