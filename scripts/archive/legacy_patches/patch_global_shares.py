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

py_patch = r'''
api_path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing/lib/api.php'
with open(api_path, 'r') as f:
    code = f.read()

target = """\t\t$shares = \\OCP\\Share::getItemShared('file', null);

\t\tif ($shares === false) {
\t\t\treturn new \\OC_OCS_Result(null, 404, 'could not get shares');
\t\t} else {
\t\t\tforeach ($shares as &$share) {
\t\t\t\tif ($share['item_type'] === 'file' && isset($share['path'])) {
\t\t\t\t\t$share['mimetype'] = \\OC_Helper::getFileNameMimeType($share['path']);
\t\t\t\t\tif (\\OC::$server->getPreviewManager()->isMimeSupported($share['mimetype'])) {
\t\t\t\t\t\t$share['isPreviewAvailable'] = true;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\treturn new \\OC_OCS_Result($shares);
\t\t}"""

replacement = """\t\t$shares = \\OCP\\Share::getItemShared('file', null);
\t\tif ($shares === false) {
\t\t\t$shares = array();
\t\t}
\t\t$folderShares = \\OCP\\Share::getItemShared('folder', null);
\t\tif (is_array($folderShares)) {
\t\t\t$shares = array_merge($shares, $folderShares);
\t\t}

\t\tforeach ($shares as &$share) {
\t\t\tif (isset($share['file_source'])) {
\t\t\t\t$fsPath = \\OC\\Files\\Filesystem::getPath($share['file_source']);
\t\t\t\tif ($fsPath) {
\t\t\t\t\t$share['path'] = $fsPath;
\t\t\t\t}
\t\t\t}
\t\t\tif ((int)$share['share_type'] === 3) {
\t\t\t\t$share['url'] = \\OCP\\Util::linkToPublic('files&t='.$share['token']);
\t\t\t\t$share['name'] = basename($share['file_target']);
\t\t\t}
\t\t\tif (!isset($share['displayname_owner']) && isset($share['uid_owner'])) {
\t\t\t\t$share['displayname_owner'] = \\OCP\\User::getDisplayName($share['uid_owner']);
\t\t\t}
\t\t\tif ($share['item_type'] === 'file' && isset($share['path'])) {
\t\t\t\t$share['mimetype'] = \\OC_Helper::getFileNameMimeType($share['path']);
\t\t\t\tif (\\OC::$server->getPreviewManager()->isMimeSupported($share['mimetype'])) {
\t\t\t\t\t$share['isPreviewAvailable'] = true;
\t\t\t\t}
\t\t\t}
\t\t}
\t\treturn new \\OC_OCS_Result($shares);"""

if target in code:
    code = code.replace(target, replacement)
    with open(api_path, 'w') as f:
        f.write(code)
    print("GLOBAL_SHARES_PATCHED_OK")
else:
    print("TARGET_NOT_FOUND")
'''

hex_str = binascii.hexlify(py_patch.encode('utf-8')).decode('ascii')
chunks = [hex_str[i:i+64] for i in range(0, len(hex_str), 64)]

s.sendall(b'> /tmp/patch_all_shares.hex\n')
ru(b'# ')

for ch in chunks:
    s.sendall(('echo -n "%s" >> /tmp/patch_all_shares.hex\n' % ch).encode('ascii'))
    import time; time.sleep(0.02)

import time; time.sleep(0.5)
s.sendall(b'echo "DONE_CHUNKS"\n')
ru(b'# ')

s.sendall(b"python -c \"import binascii; open('/tmp/patch_all_shares.py', 'wb').write(binascii.unhexlify(open('/tmp/patch_all_shares.hex').read().strip()))\" && python /tmp/patch_all_shares.py\n")
print(ru(b'# ').decode())
s.close()
