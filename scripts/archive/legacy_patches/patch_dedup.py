import socket
import binascii

s = socket.socket()
s.connect(('178.140.8.56', 34523))
def ru(p):
    b = b''
    while p not in b:
        c = s.recv(1024)
        if not c: break
        b += c
    return b

ru(b'login: ')
s.sendall(b'admin\n')
ru(b'Password: ')
s.sendall(b'12345678\n')
ru(b'$ ')
s.sendall(b'/bin/busybox su\n')
ru(b'Password: ')
s.sendall(b'12345678\n')
ru(b'# ')

py_dedup = r'''
api_path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/lib/api.php'
with open(api_path, 'r') as f:
    code = f.read()

target = """\t\t$folderShares = \\OCP\\Share::getItemShared('folder', null);
\t\tif (is_array($folderShares)) {
\t\t\t$shares = array_merge($shares, $folderShares);
\t\t}"""

replacement = """\t\t$folderShares = \\OCP\\Share::getItemShared('folder', null);
\t\tif (is_array($folderShares)) {
\t\t\t$shares = array_merge($shares, $folderShares);
\t\t}
\t\t$unique = array();
\t\tforeach ($shares as $s) {
\t\t\t$unique[$s['id']] = $s;
\t\t}
\t\t$shares = array_values($unique);"""

if target in code:
    code = code.replace(target, replacement)
    with open(api_path, 'w') as f:
        f.write(code)
    print("DEDUP_OK")
else:
    print("DEDUP_TARGET_NOT_FOUND")
'''

hex_str = binascii.hexlify(py_dedup.encode('utf-8')).decode('ascii')
chunks = [hex_str[i:i+64] for i in range(0, len(hex_str), 64)]

s.sendall(b'> /tmp/patch_dedup.hex\n')
ru(b'# ')

for ch in chunks:
    s.sendall(('echo -n "%s" >> /tmp/patch_dedup.hex\n' % ch).encode('ascii'))
    import time; time.sleep(0.02)

import time; time.sleep(0.5)
s.sendall(b'echo "DONE_CHUNKS"\n')
ru(b'# ')

s.sendall(b"python -c \"import binascii; open('/tmp/patch_dedup.py', 'wb').write(binascii.unhexlify(open('/tmp/patch_dedup.hex').read().strip()))\" && python /tmp/patch_dedup.py\n")
print(ru(b'# ').decode())
s.close()
