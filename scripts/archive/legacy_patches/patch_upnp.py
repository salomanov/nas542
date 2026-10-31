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

cmd = '''
cat << 'EOF' > /tmp/patch_upnp.py
content = open('/i-data/45f1aca1/Apps/ensure_upnp_ports.py').read()
if '34503' not in content:
    lines = content.splitlines()
    new_lines = []
    for l in lines:
        new_lines.append(l)
        if 'NAS542-HTTP-Desktop' in l:
            new_lines.append('    add_port(34503, 5003, "TCP", "NAS542-HTTPS-WebDAV")')
    open('/i-data/45f1aca1/Apps/ensure_upnp_ports.py', 'w').write('\\n'.join(new_lines) + '\\n')
EOF
python /tmp/patch_upnp.py
python /i-data/45f1aca1/Apps/ensure_upnp_ports.py
'''
s.sendall(cmd.encode('ascii'))
time.sleep(3)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
