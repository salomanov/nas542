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

# Create /i-data/45f1aca1/Apps/apps_proxy.conf
proxy_conf = '''# Reverse proxy for Entware apps under pkg_httpd
# Mounted on both :5000 (http) and :5001 (https)

ProxyRequests Off
ProxyPreserveHost On

# Syncthing GUI
ProxyPass        /apps/sync/ http://127.0.0.1:5004/
ProxyPassReverse /apps/sync/ http://127.0.0.1:5004/

# COPS (Calibre OPDS)
ProxyPass        /apps/cops/ http://127.0.0.1:5005/
ProxyPassReverse /apps/cops/ http://127.0.0.1:5005/

# AriaNg UI
ProxyPass        /apps/aria/ http://127.0.0.1:5006/
ProxyPassReverse /apps/aria/ http://127.0.0.1:5006/

# FileBrowser (baseurl /apps/fb)
ProxyPass        /apps/fb/ http://127.0.0.1:5007/
ProxyPassReverse /apps/fb/ http://127.0.0.1:5007/

# Transmission (native /transmission/ paths)
ProxyPass        /transmission/ http://127.0.0.1:5008/transmission/
ProxyPassReverse /transmission/ http://127.0.0.1:5008/transmission/

# aria2 RPC (for AriaNg)
ProxyPass        /jsonrpc http://127.0.0.1:6800/jsonrpc
ProxyPassReverse /jsonrpc http://127.0.0.1:6800/jsonrpc

<Proxy *>
    Order deny,allow
    Allow from all
</Proxy>
'''

restore_sh = '''#!/bin/sh
# Restore proxy configuration
cp /i-data/45f1aca1/Apps/apps_proxy.conf /etc/pkg_service_conf/apps_proxy.conf

CONF=/etc/pkg_service_conf/httpd2.conf
if [ -f "$CONF" ]; then
    if ! grep -q "/apps/" "$CONF"; then
        sed -i '/^AuthZyxelSkipPattern /s|$| /apps/ /transmission/ /jsonrpc|' "$CONF"
    fi
    if ! grep -q "apps_proxy.conf" "$CONF"; then
        printf '\\n# NAS542: application reverse proxy\\nInclude /etc/pkg_service_conf/apps_proxy.conf\\n' >> "$CONF"
    fi
fi

# Also ensure in Entware-ng.conf
ENT_CONF=/etc/pkg_service_conf/Entware-ng.conf
if [ -f "$ENT_CONF" ]; then
    if ! grep -q "apps_proxy.conf" "$ENT_CONF"; then
        printf '\\nInclude /etc/pkg_service_conf/apps_proxy.conf\\n' >> "$ENT_CONF"
    fi
fi

/etc/init.d/pkghttpd.sh reload
'''

s.sendall(b"cat << 'EOF' > /i-data/45f1aca1/Apps/apps_proxy.conf\n" + proxy_conf.encode() + b"\nEOF\n")
time.sleep(1)
s.sendall(b"cat << 'EOF' > /i-data/45f1aca1/Apps/restore_proxy.sh\n" + restore_sh.encode() + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /i-data/45f1aca1/Apps/restore_proxy.sh\n")
time.sleep(1)
s.sendall(b"/i-data/45f1aca1/Apps/restore_proxy.sh\n")
time.sleep(3)
# Also link to /opt/etc/init.d/S98apps-proxy
s.sendall(b"ln -sf /i-data/45f1aca1/Apps/restore_proxy.sh /opt/etc/init.d/S98apps-proxy\n")
time.sleep(1)

out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
