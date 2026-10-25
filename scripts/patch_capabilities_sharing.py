import socket
import time
import binascii

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

patch_code = r'''# -*- coding: utf-8 -*-
path = "/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/lib/private/ocs/cloud.php"
with open(path, 'r') as f:
    code = f.read()

target = """                $result['capabilities'] = array(
                        'core' => array(
                                'pollinterval' => OC_Config::getValue('pollinterval', 60),
                                ),
                        );"""

replacement = """                $result['capabilities'] = array(
                        'core' => array(
                                'pollinterval' => OC_Config::getValue('pollinterval', 60),
                                ),
                        'files' => array(
                                'bigfilechunking' => true,
                                'undelete' => true,
                                'versioning' => true,
                                ),
                        'files_sharing' => array(
                                'api_enabled' => true,
                                'public' => array(
                                        'enabled' => true,
                                        'password' => array('enforced' => false),
                                        'expire_date' => array('enabled' => false),
                                        'send_mail' => false,
                                        'upload' => true,
                                        ),
                                'user' => array('send_mail' => false),
                                'resharing' => true,
                                'group_sharing' => true,
                                'federation' => array('outgoing' => true, 'incoming' => true),
                                ),
                        );"""

if target in code:
    code = code.replace(target, replacement)
    with open(path, 'w') as f:
        f.write(code)
    print("CAPABILITIES_PATCHED_OK")
else:
    print("TARGET_NOT_FOUND")
'''

hex_data = binascii.hexlify(patch_code.encode('utf-8')).decode('ascii')
chunks = [hex_data[i:i+64] for i in range(0, len(hex_data), 64)]

s.sendall(b"> /tmp/cap_patch.hex\n")
time.sleep(0.5)

for ch in chunks:
    s.sendall(('echo "%s" >> /tmp/cap_patch.hex\n' % ch).encode('ascii'))
    time.sleep(0.04)

time.sleep(0.5)
s.sendall(b"python -c \"import binascii; open('/tmp/cap_patch.py', 'wb').write(binascii.unhexlify(open('/tmp/cap_patch.hex').read().replace('\\n','')))\" && python /tmp/cap_patch.py\n")

time.sleep(2)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
