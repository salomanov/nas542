import socket
import time
import base64

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

test_script = b'''#!/bin/sh
mkdir -p "/i-data/45f1aca1/test_utf8/\xd0\x9b\xd0\xb8\xd1\x87\xd0\xbd\xd0\xbe\xd0\xb5/\xd0\x94\xd0\xbe\xd0\xba\xd1\x83\xd0\xbc\xd0\xb5\xd0\xbd\xd1\x82\xd1\x8b"
python -c "import os; print [f.decode('utf-8') for f in os.listdir('/i-data/45f1aca1/test_utf8')]"
'''

b64 = base64.b64encode(test_script).decode('ascii')
# To prevent line wrap, write in 64 char chunks
chunks = [b64[i:i+64] for i in range(0, len(b64), 64)]

s.sendall(b"> /tmp/t.b64\n")
time.sleep(0.5)
for ch in chunks:
    s.sendall(('echo -n "%s" >> /tmp/t.b64\n' % ch).encode('ascii'))
    time.sleep(0.2)

s.sendall(b"/usr/bin/openssl enc -d -base64 -in /tmp/t.b64 -out /tmp/t.sh && chmod +x /tmp/t.sh && /tmp/t.sh\n")
time.sleep(2)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)

# Cleanup
s.sendall(b"rm -rf /i-data/45f1aca1/test_utf8 /tmp/t.b64 /tmp/t.sh\n")
time.sleep(1)
s.close()
