import socket

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

py_code = """# -*- coding: utf-8 -*-
path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/templates/public.php'
with open(path, 'rb') as f:
    data = f.read()

# Replace any corrupted badge with clean UTF-8
start = data.find(b'<div class="expiration-notice"')
if start != -1:
    end = data.find(b'</div>', start) + 6
    correct_badge = '''<div class="expiration-notice" style="margin: 15px auto; text-align: center; color: #555; font-size: 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px 15px; max-width: 420px;">
\t\t\t\t<strong>Срок действия ссылки:</strong> до <?php p(date('d.m.Y H:i', strtotime($_['expiration']))); ?>
\t\t\t</div>'''.encode('utf-8')
    data = data[:start] + correct_badge + data[end:]
    with open(path, 'wb') as f:
        f.write(data)
    print("BADGE_FIXED_UTF8")
else:
    print("BADGE_NOT_FOUND")
"""

import binascii
hex_str = binascii.hexlify(py_code.encode('utf-8')).decode('ascii')
s.sendall(('echo "%s" > /tmp/fix_badge.hex\n' % hex_str).encode('ascii'))
ru(b'# ')
s.sendall(b"python -c \"import binascii; open('/tmp/fix_badge.py', 'wb').write(binascii.unhexlify(open('/tmp/fix_badge.hex').read().strip()))\" && python /tmp/fix_badge.py\n")
print(ru(b'# ').decode())

s.close()
