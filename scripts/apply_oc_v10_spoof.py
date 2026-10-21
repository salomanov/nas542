import socket
import time

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

patch_script = r'''#!/bin/sh
set -e
OC_DIR="/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud"

# 1. Backup files
[ -f "$OC_DIR/status.php.bak-v10" ] || cp -p "$OC_DIR/status.php" "$OC_DIR/status.php.bak-v10"
[ -f "$OC_DIR/lib/private/ocs/cloud.php.bak-v10" ] || cp -p "$OC_DIR/lib/private/ocs/cloud.php" "$OC_DIR/lib/private/ocs/cloud.php.bak-v10"

# 2. Patch status.php: replace output version with 10.13.4.1
cat << 'EOF' > "$OC_DIR/status.php"
<?php
try {
        require_once 'lib/base.php';

        if(OC_Config::getValue('installed')==1) $installed='true'; else $installed='false';
        $values=array(
                'installed'=>true,
                'maintenance'=>false,
                'needsDbUpgrade'=>false,
                'version'=>'10.13.4.1',
                'versionstring'=>'10.13.4',
                'edition'=>'',
                'productname'=>'ownCloud');
        if (OC::$CLI) {
                print_r($values);
        } else {
                echo json_encode($values);
        }
} catch (Exception $ex) {
        OC_Response::setStatus(OC_Response::STATUS_INTERNAL_SERVER_ERROR);
        \OCP\Util::writeLog('remote', $ex->getMessage(), \OCP\Util::FATAL);
}
EOF

# 3. Patch lib/private/ocs/cloud.php to report 10.13.4 in capabilities
sed -i "s/'major' => \$major/'major' => 10/" "$OC_DIR/lib/private/ocs/cloud.php"
sed -i "s/'minor' => \$minor/'minor' => 13/" "$OC_DIR/lib/private/ocs/cloud.php"
sed -i "s/'micro' => \$micro/'micro' => 4/" "$OC_DIR/lib/private/ocs/cloud.php"
sed -i "s/'string' => OC_Util::getVersionString()/'string' => '10.13.4'/" "$OC_DIR/lib/private/ocs/cloud.php"

echo "PATCH_APPLIED"
'''

s.sendall(b"cat << 'EOF' > /tmp/patch_oc_v10.sh\n" + patch_script.encode() + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /tmp/patch_oc_v10.sh && /tmp/patch_oc_v10.sh\n")
time.sleep(2)
out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
