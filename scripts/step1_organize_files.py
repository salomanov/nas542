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

organize_script = r'''#!/bin/sh
set -e

echo "=== 1. Setup Disk 3 (Медиа) ==="
mkdir -p "/i-data/dadf1c38/Медиа/Фильмы"
mkdir -p "/i-data/dadf1c38/Медиа/Музыка"
mkdir -p "/i-data/dadf1c38/Медиа/Книги"
mkdir -p "/i-data/dadf1c38/Медиа/Загрузки"
chown -R admin:everyone "/i-data/dadf1c38/Медиа"
chmod -R 777 "/i-data/dadf1c38/Медиа"

# Move Green Book to Disk 3
if [ -f "/i-data/8c0fa088/1/Green Book (2018).mkv" ]; then
    echo "Moving Green Book to Disk 3..."
    mv "/i-data/8c0fa088/1/Green Book (2018).mkv" "/i-data/dadf1c38/Медиа/Фильмы/"
fi

echo "=== 2. Setup Disk 1 (Личное) ==="
mkdir -p "/i-data/45f1aca1/Личное/Документы"
mkdir -p "/i-data/45f1aca1/Личное/Фото"
mkdir -p "/i-data/45f1aca1/Личное/Видео"
chown -R admin:everyone "/i-data/45f1aca1/Личное"
chmod -R 777 "/i-data/45f1aca1/Личное"

# Move videos to Disk 1
if [ -f "/i-data/8c0fa088/1/VID_20261004_215242.mp4" ]; then
    mv "/i-data/8c0fa088/1/VID_20261004_215242.mp4" "/i-data/45f1aca1/Личное/Видео/"
fi
if [ -f "/i-data/d4877b70/disk4/VID_20260812_094514_213.mp4" ]; then
    mv "/i-data/d4877b70/disk4/VID_20260812_094514_213.mp4" "/i-data/45f1aca1/Личное/Видео/"
fi

echo "=== 3. Setup Disk 2 (Работа) ==="
mkdir -p "/i-data/8c0fa088/Работа/Проекты"
mkdir -p "/i-data/8c0fa088/Работа/Документы"
mkdir -p "/i-data/8c0fa088/Работа/Обмен"
chown -R admin:everyone "/i-data/8c0fa088/Работа"
chmod -R 777 "/i-data/8c0fa088/Работа"

# Clean up unwanted apk and temporary folder 1
rm -rf "/i-data/8c0fa088/1"

echo "=== 4. Setup Disk 4 (Бэкапы) ==="
mkdir -p "/i-data/d4877b70/Бэкапы/Компьютеры"
mkdir -p "/i-data/d4877b70/Бэкапы/Архивы_NAS"
rm -rf "/i-data/d4877b70/.PKG"
chown -R admin:everyone "/i-data/d4877b70/Бэкапы"
chmod -R 777 "/i-data/d4877b70/Бэкапы"

echo "=== 5. Clean macOS junk ==="
find /i-data/ -name ".DS_Store" -delete 2>/dev/null || true
find /i-data/ -name "._*" -delete 2>/dev/null || true

echo "ORGANIZATION_COMPLETE"
'''

s.sendall(b"cat << 'EOF' > /tmp/do_organize.sh\n" + organize_script.encode('utf-8') + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /tmp/do_organize.sh && /tmp/do_organize.sh\n")
time.sleep(5)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
