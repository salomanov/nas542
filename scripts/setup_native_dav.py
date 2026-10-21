# -*- coding: utf-8 -*-
import socket
import time
import binascii

remote_python = u'''# -*- coding: utf-8 -*-
with open('/etc/service_conf/httpd_dav_auth.conf', 'r') as f:
    conf = f.read()

dav_block = """
####### [ Storage - Unified 4 Disks WebDAV ] #########
Alias "/webdav" "/i-data/45f1aca1/Storage"

<Directory "/i-data/45f1aca1/Storage">
        Options FollowSymLinks
        AllowOverride All
        Order Allow,Deny
        Allow from all
</Directory>

<Location "/webdav">
        IndexOptions Charset=UTF-8
        Dav On
        DavMinTimeout 600
        DavDepthInfinity on
        AuthType Basic
        AuthName "DAV-Storage"
        AuthBasicProvider cache
        AuthnCacheProvider external
        AuthnCacheTimeout 10
        AuthExternal pwauth
        AuthzUnixgroup on
        <limit GET HEAD OPTIONS REPORT PROPFIND>
                require user "admin"
        </limit>
        <LimitExcept get head options>
                require user "admin"
        </LimitExcept>
</Location>
"""

if 'Alias "/webdav" "/i-data/45f1aca1/Storage"' not in conf:
    with open('/etc/service_conf/httpd_dav_auth.conf', 'a') as f:
        f.write(dav_block)

import os
os.system("/etc/init.d/davhttpd.sh reload")
print("DAV_CONFIGURED_AND_RELOADED")
'''.encode('utf-8')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(15)
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

hex_data = binascii.hexlify(remote_python).decode('ascii')
chunks = [hex_data[i:i+64] for i in range(0, len(hex_data), 64)]

s.sendall(b"> /tmp/dav_add.hex\n")
time.sleep(0.5)

for ch in chunks:
    s.sendall(('echo "%s" >> /tmp/dav_add.hex\n' % ch).encode('ascii'))
    time.sleep(0.04)

time.sleep(0.5)
s.sendall(b"python -c \"import binascii; open('/tmp/dav_add.py', 'wb').write(binascii.unhexlify(open('/tmp/dav_add.hex').read().replace('\\n','')))\" && python /tmp/dav_add.py\n")

time.sleep(3)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
