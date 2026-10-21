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

script_body = '''#!/usr/bin/env python
# Script to ensure UPnP port mappings in Keenetic router
import urllib2
import time

def add_port(ext_port, int_port, proto="TCP", desc="NAS542"):
    url = "http://192.168.1.1:1900/ctl/L3F"
    body = """<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:AddPortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
<NewRemoteHost></NewRemoteHost>
<NewExternalPort>%d</NewExternalPort>
<NewProtocol>%s</NewProtocol>
<NewInternalPort>%d</NewInternalPort>
<NewInternalClient>192.168.1.50</NewInternalClient>
<NewEnabled>1</NewEnabled>
<NewPortMappingDescription>%s</NewPortMappingDescription>
<NewLeaseDuration>0</NewLeaseDuration>
</u:AddPortMapping>
</s:Body>
</s:Envelope>""" % (ext_port, proto, int_port, desc)

    req = urllib2.Request(url, data=body, headers={
        "SOAPAction": '"urn:schemas-upnp-org:service:WANIPConnection:1#AddPortMapping"',
        "Content-Type": 'text/xml; charset="utf-8"'
    })
    try:
        resp = urllib2.urlopen(req, timeout=5).read()
        print "Added port %d -> %d: SUCCESS" % (ext_port, int_port)
    except Exception as e:
        print "Failed port %d: %s" % (ext_port, e)

if __name__ == '__main__':
    add_port(34501, 5001, "TCP", "NAS542-HTTPS-Apps")
    add_port(34502, 80, "TCP", "NAS542-HTTP-Desktop")
    add_port(34522, 22, "TCP", "NAS542-SSH")
    add_port(34523, 23, "TCP", "NAS542-TELNET")
'''

s.sendall(b"cat << 'EOF' > /i-data/45f1aca1/Apps/ensure_upnp_ports.py\n" + script_body.encode() + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /i-data/45f1aca1/Apps/ensure_upnp_ports.py\n")
time.sleep(1)
# Create init.d script in /opt/etc/init.d/S99upnp-ports
init_body = '''#!/bin/sh
case "$1" in
    start|restart|reload)
        /usr/bin/python /i-data/45f1aca1/Apps/ensure_upnp_ports.py >/dev/null 2>&1 &
        ;;
    stop)
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
exit 0
'''
s.sendall(b"cat << 'EOF' > /opt/etc/init.d/S99upnp-ports\n" + init_body.encode() + b"\nEOF\n")
time.sleep(1)
s.sendall(b"chmod +x /opt/etc/init.d/S99upnp-ports\n")
time.sleep(1)
out = s.recv(4096).decode('ascii', errors='ignore')
print(out)
s.close()
