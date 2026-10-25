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
remote_path = '/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/remote.php'
with open(remote_path, 'r') as f:
    code = f.read()

target = """\t\t\t$__h = implode("\\n", headers_list());
\t\t\tif (stripos($__h, "xml") === false) {
\t\t\t\treturn $__buf;
\t\t\t}
\t\t\treturn str_replace("/remote.php/webdav/", "/remote.php/dav/files/" . $GLOBALS["OC_DAV_SHIM_USER"] . "/", $__buf);
\t\t}, 1048576);"""

replacement = """\t\t\t$__h = implode("\\n", headers_list());
\t\t\tif (stripos($__h, "xml") === false) {
\t\t\t\treturn $__buf;
\t\t\t}
\t\t\t$__buf = str_replace("/remote.php/webdav/", "/remote.php/dav/files/" . $GLOBALS["OC_DAV_SHIM_USER"] . "/", $__buf);

\t\t\tif (strpos($__buf, '<oc:share-types/>') !== false || strpos($__buf, '<oc:id>') !== false) {
\t\t\t\tstatic $sharedMap = null;
\t\t\t\tif ($sharedMap === null) {
\t\t\t\t\t$sharedMap = array();
\t\t\t\t\ttry {
\t\t\t\t\t\t$q = \\OC_DB::prepare('SELECT file_source, share_type FROM `*PREFIX*share` WHERE uid_owner = ?');
\t\t\t\t\t\t$r = $q->execute(array($GLOBALS["OC_DAV_SHIM_USER"]));
\t\t\t\t\t\twhile ($row = $r->fetchRow()) {
\t\t\t\t\t\t\t$fid = (int)$row['file_source'];
\t\t\t\t\t\tif (!isset($sharedMap[$fid])) {
\t\t\t\t\t\t\t$sharedMap[$fid] = array();
\t\t\t\t\t\t}
\t\t\t\t\t\t$sharedMap[$fid][] = (int)$row['share_type'];
\t\t\t\t\t\t}
\t\t\t\t\t} catch (\\Exception $e) {}
\t\t\t\t}
\t\t\t\t$__buf = preg_replace_callback('#<d:response>.*?</d:response>#s', function($m) use ($sharedMap) {
\t\t\t\t\t$resp = $m[0];
\t\t\t\t\tif (preg_match('#<oc:id>(\\\\d{8})#', $resp, $id_m)) {
\t\t\t\t\t\t$fid = (int)$id_m[1];
\t\t\t\t\t\t$stypes = isset($sharedMap[$fid]) ? $sharedMap[$fid] : array();
\t\t\t\t\t\tif (!empty($stypes)) {
\t\t\t\t\t\t\t$st_xml = '<oc:share-types>';
\t\t\t\t\t\t\tforeach ($stypes as $t) {
\t\t\t\t\t\t\t\t$st_xml .= '<oc:share-type>' . $t . '</oc:share-type>';
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t$st_xml .= '</oc:share-types>';
\t\t\t\t\t\t} else {
\t\t\t\t\t\t\t$st_xml = '<oc:share-types/>';
\t\t\t\t\t\t}
\t\t\t\t\t\t$resp = preg_replace('#(<d:propstat>\\\\s*<d:prop>)#s', '$1' . $st_xml, $resp, 1);
\t\t\t\t\t\t$resp = str_replace('<oc:share-types/>', '', $resp);
\t\t\t\t\t}
\t\t\t\t\treturn $resp;
\t\t\t\t}, $__buf);
\t\t\t}
\t\t\treturn $__buf;
\t\t}, 1048576);"""

if target in code:
    code = code.replace(target, replacement)
    with open(remote_path, 'w') as f:
        f.write(code)
    print("REMOTE_PHP_PATCHED_OK")
else:
    print("TARGET_NOT_FOUND")
'''

hex_str = binascii.hexlify(py_patch.encode('utf-8')).decode('ascii')
chunks = [hex_str[i:i+64] for i in range(0, len(hex_str), 64)]

s.sendall(b'> /tmp/patch_remote.hex\n')
ru(b'# ')

for ch in chunks:
    s.sendall(('echo -n "%s" >> /tmp/patch_remote.hex\n' % ch).encode('ascii'))
    import time; time.sleep(0.02)

import time; time.sleep(0.5)
s.sendall(b'echo "DONE_CHUNKS"\n')
ru(b'# ')

s.sendall(b"python -c \"import binascii; open('/tmp/patch_remote.py', 'wb').write(binascii.unhexlify(open('/tmp/patch_remote.hex').read().strip()))\" && python /tmp/patch_remote.py\n")
print(ru(b'# ').decode())
s.close()
