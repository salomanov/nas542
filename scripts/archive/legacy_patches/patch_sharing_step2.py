import socket
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

patch_code = r'''# -*- coding: utf-8 -*-
import shutil

# --- 1. Patch apps/files_sharing/lib/api.php ---
api_path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/lib/api.php'

with open(api_path, 'r') as f:
    api_code = f.read()

target_collect_shares = """\tprivate static function collectShares($params) {

\t\t$itemSource = $params['itemSource'];
\t\t$itemType = $params['itemType'];
\t\t$getSpecificShare = isset($params['specificShare']) ? $params['specificShare'] : false;

\t\tif ($itemSource !== null) {
\t\t\t$shares = \\OCP\\Share::getItemShared($itemType, $itemSource);
\t\t\t$receivedFrom = \\OCP\\Share::getItemSharedWithBySource($itemType, $itemSource);
\t\t\t// if a specific share was specified only return this one
\t\t\tif ($getSpecificShare === true) {
\t\t\t\tforeach ($shares as $share) {
\t\t\t\t\tif ($share['id'] === (int) $params['id']) {
\t\t\t\t\t\t$shares = array('element' => $share);
\t\t\t\t\t\tbreak;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t} else {
\t\t\t\t$path = $params['path'];
\t\t\t\tforeach ($shares as $key => $share) {
\t\t\t\t\t$shares[$key]['path'] = $path;
\t\t\t\t\tif ((int)$share['share_type'] === 3) {
\t\t\t\t\t\t$shares[$key]['url'] = \\OCP\\Util::linkToPublic('files&t='.$share['token']);
\t\t\t\t\t\t$shares[$key]['name'] = basename($share['file_target']);
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}"""

replacement_collect_shares = """\tprivate static function collectShares($params) {

\t\t$itemSource = $params['itemSource'];
\t\t$itemType = $params['itemType'];
\t\t$getSpecificShare = isset($params['specificShare']) ? $params['specificShare'] : false;

\t\tif ($itemSource !== null) {
\t\t\t$shares = \\OCP\\Share::getItemShared($itemType, $itemSource);
\t\t\t$receivedFrom = \\OCP\\Share::getItemSharedWithBySource($itemType, $itemSource);

\t\t\t$path = isset($params['path']) ? $params['path'] : null;
\t\t\t$formatted = array();
\t\t\tforeach ($shares as $share) {
\t\t\t\tif ($getSpecificShare === true && (int)$share['id'] !== (int)$params['id']) {
\t\t\t\t\tcontinue;
\t\t\t\t}
\t\t\t\t$item = $share;
\t\t\t\tif ($path) {
\t\t\t\t\t$item['path'] = $path;
\t\t\t\t} elseif (isset($item['file_target'])) {
\t\t\t\t\t$item['path'] = $item['file_target'];
\t\t\t\t}
\t\t\t\tif ((int)$item['share_type'] === 3) {
\t\t\t\t\t$item['url'] = \\OCP\\Util::linkToPublic('files&t='.$item['token']);
\t\t\t\t\t$item['name'] = basename($item['file_target']);
\t\t\t\t}
\t\t\t\tif (!isset($item['displayname_owner']) && isset($item['uid_owner'])) {
\t\t\t\t\t$item['displayname_owner'] = \\OCP\\User::getDisplayName($item['uid_owner']);
\t\t\t\t}
\t\t\t\t$formatted[] = $item;
\t\t\t}

\t\t\tif ($getSpecificShare === true) {
\t\t\t\tif (empty($formatted)) {
\t\t\t\t\treturn new \\OC_OCS_Result(null, 404, 'share doesn\\'t exist');
\t\t\t\t}
\t\t\t\treturn new \\OC_OCS_Result($formatted);
\t\t\t}

\t\t\t$shares = $formatted;"""

if target_collect_shares in api_code:
    api_code = api_code.replace(target_collect_shares, replacement_collect_shares)
    with open(api_path, 'w') as f:
        f.write(api_code)
    print("API_PHP_PATCHED_OK")
else:
    print("API_PHP_TARGET_NOT_FOUND")

# --- 2. Patch public.php to pass expiration to template ---
pub_path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/public.php'
with open(pub_path, 'r') as f:
    pub_code = f.read()

target_pub = "$tmpl->assign('previewEnabled', \\OC::$server->getConfig()->getSystemValue('enable_previews', true));"
replace_pub = "$tmpl->assign('previewEnabled', \\OC::$server->getConfig()->getSystemValue('enable_previews', true));\n\t\t$tmpl->assign('expiration', isset($linkItem['expiration']) ? $linkItem['expiration'] : null);"

if target_pub in pub_code:
    pub_code = pub_code.replace(target_pub, replace_pub)
    with open(pub_path, 'w') as f:
        f.write(pub_code)
    print("PUBLIC_PHP_PATCHED_OK")
else:
    print("PUBLIC_PHP_TARGET_NOT_FOUND")

# --- 3. Patch templates/public.php to render expiration badge ---
tmpl_path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/templates/public.php'
with open(tmpl_path, 'r') as f:
    tmpl_code = f.read()

target_tmpl = '<div class="directLink">'
replace_tmpl = '<?php if (!empty($_[\'expiration\'])): ?>\n\t\t\t<div class="expiration-notice" style="margin: 15px auto; text-align: center; color: #555; font-size: 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px 15px; max-width: 420px;">\n\t\t\t\t<strong>Срок действия ссылки:</strong> до <?php p(date(\'d.m.Y H:i\', strtotime($_[\'expiration\']))); ?>\n\t\t\t</div>\n\t\t\t<?php endif; ?>\n\t\t\t<div class="directLink">'

if target_tmpl in tmpl_code:
    tmpl_code = tmpl_code.replace(target_tmpl, replace_tmpl)
    with open(tmpl_path, 'w') as f:
        f.write(tmpl_code)
    print("TEMPLATES_PUBLIC_PATCHED_OK")
else:
    print("TEMPLATES_PUBLIC_TARGET_NOT_FOUND")
'''

hex_str = binascii.hexlify(patch_code.encode('utf-8')).decode('ascii')
chunks = [hex_str[i:i+64] for i in range(0, len(hex_str), 64)]

print("Clearing /tmp/patch_step2.hex")
tc.cmd('> /tmp/patch_step2.hex')

for ch in chunks:
    tc.s.sendall(('echo -n "%s" >> /tmp/patch_step2.hex\n' % ch).encode('ascii'))
    import time; time.sleep(0.02)

import time; time.sleep(0.5)
tc.cmd('echo "DONE_CHUNKS"')

print("Decoding and running patch on NAS...")
print(tc.cmd('python -c "import binascii; open(\'/tmp/patch_step2.py\', \'wb\').write(binascii.unhexlify(open(\'/tmp/patch_step2.hex\').read().strip()))"'))
print(tc.cmd('python /tmp/patch_step2.py'))

tc.close()
