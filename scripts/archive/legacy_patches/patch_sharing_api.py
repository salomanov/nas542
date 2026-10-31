import socket

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

patch_code = r'''
import shutil

api_path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/lib/api.php'
shutil.copyfile(api_path, api_path + '.bak-oc10compat')

with open(api_path, 'r') as f:
    code = f.read()

# 1. Support JSON body in createShare if sent as application/json
target_create_start = """\tpublic static function createShare($params) {\n\n\t\t$path = isset($_POST['path']) ? $_POST['path'] : null;"""
replace_create_start = """\tpublic static function createShare($params) {

\t\t$raw = file_get_contents('php://input');
\t\tif (!empty($raw)) {
\t\t\t$json = json_decode($raw, true);
\t\t\tif (is_array($json)) {
\t\t\t\t$_POST = array_merge($_POST, $json);
\t\t\t}
\t\t}

\t\t$path = isset($_POST['path']) ? $_POST['path'] : null;"""

# 2. Enrich createShare return with full share fields
target_create_return = """\t\tif ($token) {
\t\t\t$data = array();
\t\t\t$data['id'] = 'unknown';
\t\t\t$shares = \\OCP\\Share::getItemShared($itemType, $itemSource);
\t\t\tif(is_string($token)) { //public link share
\t\t\t\tforeach ($shares as $share) {
\t\t\t\t\tif ($share['token'] === $token) {
\t\t\t\t\t\t$data['id'] = $share['id'];
\t\t\t\t\t\tbreak;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\t$url = \\OCP\\Util::linkToPublic('files&t='.$token);
\t\t\t\t$data['url'] = $url; // '&' gets encoded to $amp;
\t\t\t\t$data['token'] = $token;

\t\t\t} else {
\t\t\t\tforeach ($shares as $share) {
\t\t\t\t\tif ($share['share_with'] === $shareWith && $share['share_type'] === $shareType) {
\t\t\t\t\t\t$data['id'] = $share['id'];
\t\t\t\t\t\tbreak;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\treturn new \\OC_OCS_Result($data);"""

replace_create_return = """\t\tif ($token) {
\t\t\t$shares = \\OCP\\Share::getItemShared($itemType, $itemSource);
\t\t\t$matchedShare = null;
\t\t\tif(is_string($token)) { //public link share
\t\t\t\tforeach ($shares as $share) {
\t\t\t\t\tif ($share['token'] === $token) {
\t\t\t\t\t\t$matchedShare = $share;
\t\t\t\t\t\tbreak;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t} else {
\t\t\t\tforeach ($shares as $share) {
\t\t\t\t\tif ($share['share_with'] === $shareWith && $share['share_type'] === $shareType) {
\t\t\t\t\t\t$matchedShare = $share;
\t\t\t\t\t\tbreak;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}

\t\t\tif ($matchedShare) {
\t\t\t\t$data = $matchedShare;
\t\t\t} else {
\t\t\t\t$data = array('id' => 'unknown', 'share_type' => $shareType);
\t\t\t}

\t\t\tif (isset($_POST['expireDate']) && !empty($_POST['expireDate'])) {
\t\t\t\t\\OCP\\Share::setExpirationDate($itemType, $itemSource, $_POST['expireDate']);
\t\t\t\t$data['expiration'] = $_POST['expireDate'];
\t\t\t}

\t\t\t$data['path'] = $path;
\t\t\tif (is_string($token)) {
\t\t\t\t$data['url'] = \\OCP\\Util::linkToPublic('files&t='.$token);
\t\t\t\t$data['token'] = $token;
\t\t\t\t$data['name'] = (isset($_POST['name']) && !empty($_POST['name'])) ? $_POST['name'] : basename($path);
\t\t\t}
\t\t\tif (!isset($data['displayname_owner']) && isset($data['uid_owner'])) {
\t\t\t\t$data['displayname_owner'] = \\OCP\\User::getDisplayName($data['uid_owner']);
\t\t\t}
\t\t\treturn new \\OC_OCS_Result($data);"""

# 3. Enrich collectShares with url and name for link shares
target_collect = """\t\t\t\t$path = $params['path'];
\t\t\t\tforeach ($shares as $key => $share) {
\t\t\t\t\t$shares[$key]['path'] = $path;
\t\t\t\t}"""

replace_collect = """\t\t\t\t$path = $params['path'];
\t\t\t\tforeach ($shares as $key => $share) {
\t\t\t\t\t$shares[$key]['path'] = $path;
\t\t\t\t\tif ((int)$share['share_type'] === 3) {
\t\t\t\t\t\t$shares[$key]['url'] = \\OCP\\Util::linkToPublic('files&t='.$share['token']);
\t\t\t\t\t\t$shares[$key]['name'] = basename($share['file_target']);
\t\t\t\t\t}
\t\t\t\t}"""

errs = []
if target_create_start in code:
    code = code.replace(target_create_start, replace_create_start)
    print("PATCH 1 OK")
else:
    errs.append("TARGET 1 NOT FOUND")

if target_create_return in code:
    code = code.replace(target_create_return, replace_create_return)
    print("PATCH 2 OK")
else:
    errs.append("TARGET 2 NOT FOUND")

if target_collect in code:
    code = code.replace(target_collect, replace_collect)
    print("PATCH 3 OK")
else:
    errs.append("TARGET 3 NOT FOUND")

if not errs:
    with open(api_path, 'w') as f:
        f.write(code)
    print("ALL_PATCHES_APPLIED_SUCCESSFULLY")
else:
    print("ERRORS:", errs)
'''

import binascii
hex_str = binascii.hexlify(patch_code.encode('utf-8')).decode('ascii')
chunks = [hex_str[i:i+64] for i in range(0, len(hex_str), 64)]

print("Clearing /tmp/patch_api.hex")
tc.cmd('> /tmp/patch_api.hex')

for ch in chunks:
    tc.s.sendall(('echo -n "%s" >> /tmp/patch_api.hex\n' % ch).encode('ascii'))
    import time; time.sleep(0.02)

import time; time.sleep(0.5)
tc.cmd('echo "DONE_CHUNKS"')

print("Decoding and executing patch on NAS...")
print(tc.cmd('python -c "import binascii; open(\'/tmp/patch_api.py\', \'wb\').write(binascii.unhexlify(open(\'/tmp/patch_api.hex\').read().strip()))"'))
print(tc.cmd('python /tmp/patch_api.py'))

tc.close()
