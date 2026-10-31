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

commands = [
    b"sed -i \"s/'major' => \$major/'major' => 10/\" /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/lib/private/ocs/cloud.php\n",
    b"sed -i \"s/'minor' => \$minor/'minor' => 13/\" /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/lib/private/ocs/cloud.php\n",
    b"sed -i \"s/'micro' => \$micro/'micro' => 4/\" /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/lib/private/ocs/cloud.php\n",
    b"sed -i \"s/'string' => OC_Util::getVersionString()/'string' => '10.13.4'/\" /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/lib/private/ocs/cloud.php\n"
]

for cmd in commands:
    s.sendall(cmd)
    time.sleep(1)

out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
