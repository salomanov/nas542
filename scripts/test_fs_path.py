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

fix_tmpl_script = r'''
path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/templates/public.php'
with open(path, 'rb') as f:
    c = f.read()

start = c.find(b'<div class="expiration-notice"')
if start != -1:
    end = c.find(b'</div>', start) + 6
    correct = b"""<div class="expiration-notice" style="margin: 15px auto; text-align: center; color: #555; font-size: 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px 15px; max-width: 420px;">
\t\t\t\t<strong>&#1057;&#1088;&#1086;&#1082; &#1076;&#1077;&#1081;&#1089;&#1090;&#1074;&#1080;&#1103; &#1089;&#1089;&#1099;&#1083;&#1082;&#1080;:</strong> &#1076;&#1086; <?php p(date('d.m.Y H:i', strtotime($_['expiration']))); ?>
\t\t\t</div>"""
    c = c[:start] + correct + c[end:]
    with open(path, 'wb') as f:
        f.write(c)
    print("HTML_ENTITIES_BADGE_OK")
else:
    print("START_NOT_FOUND")
'''

s.sendall(b"cat << 'EOF' > /tmp/fix_badge_clean.py\n" + fix_tmpl_script.encode('ascii') + b"\nEOF\n")
ru(b'# ')

s.sendall(b"python /tmp/fix_badge_clean.py\n")
print(ru(b'# ').decode())

s.close()
