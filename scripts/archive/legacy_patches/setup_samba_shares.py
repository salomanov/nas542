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

update_samba_script = '''#!/bin/sh
CONF="/etc/samba/smb.conf"
[ -f "$CONF.bak-shares" ] || cp -p "$CONF" "$CONF.bak-shares"

# Remove old section [1]
sed -i '/^\[1\]/,/^\[/ { /^\[1\]/d; /^\[/!d; }' "$CONF"

# Append clean shares if not present
if ! grep -q "^\[Personal\]" "$CONF"; then
cat << 'EOF' >> "$CONF"

[Personal]
        path = /i-data/45f1aca1/Personal
        follow symlinks = yes
        strict allocate = yes
        allocation roundup size = 0
        aio write size = 4096
        comment = "Личное (Диск 1)"
        browseable = yes
        valid users = "admin" "pc-guest"
        guest ok = yes
        write ok = yes

[Work]
        path = /i-data/8c0fa088/Work
        follow symlinks = yes
        strict allocate = yes
        allocation roundup size = 0
        aio write size = 4096
        comment = "Работа (Диск 2)"
        browseable = yes
        valid users = "admin" "pc-guest"
        guest ok = yes
        write ok = yes

[Media]
        path = /i-data/dadf1c38/Media
        follow symlinks = yes
        strict allocate = yes
        allocation roundup size = 0
        aio write size = 4096
        comment = "Медиатека (Диск 3)"
        browseable = yes
        valid users = "admin" "pc-guest"
        guest ok = yes
        write ok = yes

[Backup]
        path = /i-data/d4877b70/Backup
        follow symlinks = yes
        strict allocate = yes
        allocation roundup size = 0
        aio write size = 4096
        comment = "Бэкапы (Диск 4)"
        browseable = yes
        valid users = "admin" "pc-guest"
        guest ok = yes
        write ok = yes
EOF
fi

# Reload Samba
killall -HUP smbd 2>/dev/null || true
echo "SAMBA_UPDATED"
'''

s.sendall(b"cat << 'EOF' > /tmp/update_samba.sh\n" + update_samba_script.encode('utf-8') + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /tmp/update_samba.sh && /tmp/update_samba.sh\n")
time.sleep(2)
out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
