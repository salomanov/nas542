import socket
import time
import binascii

class TelnetClient:
    def __init__(self, host='178.140.8.56', port=34523):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(15)
        self.s.connect((host, port))
        self.read_until(b'login: ')
        self.s.sendall(b'admin\n')
        self.read_until(b'Password: ')
        self.s.sendall(b'12345678\n')
        self.read_until(b'$ ')
        self.s.sendall(b'/bin/busybox su\n')
        self.read_until(b'Password: ')
        self.s.sendall(b'12345678\n')
        self.read_until(b'# ')

    def read_until(self, expected):
        buf = b''
        while expected not in buf:
            chunk = self.s.recv(1024)
            if not chunk:
                break
            buf += chunk
        return buf

    def cmd(self, command):
        self.s.sendall(command.encode('utf-8') + b'\n')
        res = self.read_until(b'# ')
        return res.decode('utf-8', errors='ignore')

    def close(self):
        self.s.close()

tc = TelnetClient()

patch_script = r"""
import shutil

path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/lib/private/ocs/cloud.php'
shutil.copyfile(path, path + '.bak-sharing')

with open(path, 'r') as f:
    code = f.read()

target = "\t\t$result['capabilities'] = array(\n\t\t\t'core' => array(\n\t\t\t\t'pollinterval' => OC_Config::getValue('pollinterval', 60),\n\t\t\t\t),\n\t\t\t);"

replacement = '''\t\t$result['capabilities'] = array(
\t\t\t'core' => array(
\t\t\t\t'pollinterval' => OC_Config::getValue('pollinterval', 60),
\t\t\t\t),
\t\t\t'files_sharing' => array(
\t\t\t\t'api_enabled' => true,
\t\t\t\t'public' => array(
\t\t\t\t\t'enabled' => true,
\t\t\t\t\t'password' => array('enforced' => false),
\t\t\t\t\t'expire_date' => array('enabled' => false),
\t\t\t\t\t'send_mail' => false,
\t\t\t\t\t'upload' => true,
\t\t\t\t\t),
\t\t\t\t'user' => array('send_mail' => false),
\t\t\t\t'resharing' => true,
\t\t\t\t'group_sharing' => true,
\t\t\t\t'federation' => array('outgoing' => true, 'incoming' => true),
\t\t\t\t),
\t\t\t);'''

if target in code:
    code = code.replace(target, replacement)
    with open(path, 'w') as f:
        f.write(code)
    print('SUCCESS_PATCHED')
else:
    print('TARGET_NOT_FOUND')
"""

hex_str = binascii.hexlify(patch_script.encode('utf-8')).decode('ascii')
chunks = [hex_str[i:i+64] for i in range(0, len(hex_str), 64)]

print("Clearing /tmp/do_patch.hex")
tc.cmd('> /tmp/do_patch.hex')

for chunk in chunks:
    tc.s.sendall(('echo -n "%s" >> /tmp/do_patch.hex\n' % chunk).encode('ascii'))
    time.sleep(0.03)

# Clear any buffer left from rapid echoes
time.sleep(1)
tc.cmd('echo "DONE_CHUNKS"')

print("Decoding script on NAS...")
print(tc.cmd('python -c "import binascii; open(\'/tmp/do_patch.py\', \'wb\').write(binascii.unhexlify(open(\'/tmp/do_patch.hex\').read().strip()))"'))
print("Executing script on NAS...")
print(tc.cmd('python /tmp/do_patch.py'))

tc.close()
