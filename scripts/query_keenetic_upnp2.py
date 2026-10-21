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

py2_code = '''import urllib2
import re

desc = urllib2.urlopen("http://192.168.1.1:1900/rootDesc.xml", timeout=5).read()
print "Desc read len:", len(desc)

m = re.search(r"<controlURL>(.*?)</controlURL>", desc)
control_url = m.group(1) if m else "/ctl/IPConn"
if not control_url.startswith("/"):
    control_url = "/" + control_url

full_url = "http://192.168.1.1:1900" + control_url
print "Control URL:", full_url

for idx in range(30):
    body = """<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:GetGenericPortMappingEntry xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
<NewPortMappingIndex>%d</NewPortMappingIndex>
</u:GetGenericPortMappingEntry>
</s:Body>
</s:Envelope>""" % idx
    req = urllib2.Request(full_url, data=body, headers={
        "SOAPAction": '"urn:schemas-upnp-org:service:WANIPConnection:1#GetGenericPortMappingEntry"',
        "Content-Type": 'text/xml; charset="utf-8"'
    })
    try:
        resp = urllib2.urlopen(req, timeout=3).read()
        ext_port = re.search(r"<NewExternalPort>(\d+)</NewExternalPort>", resp)
        int_port = re.search(r"<NewInternalPort>(\d+)</NewInternalPort>", resp)
        proto = re.search(r"<NewProtocol>(.*?)</NewProtocol>", resp)
        client = re.search(r"<NewInternalClient>(.*?)</NewInternalClient>", resp)
        desc_p = re.search(r"<NewPortMappingDescription>(.*?)</NewPortMappingDescription>", resp)
        p_str = proto.group(1) if proto else ""
        ext_str = ext_port.group(1) if ext_port else ""
        cl_str = client.group(1) if client else ""
        int_str = int_port.group(1) if int_port else ""
        d_str = desc_p.group(1) if desc_p else ""
        print "[%d] %s WAN:%s -> %s:%s (%s)" % (idx, p_str, ext_str, cl_str, int_str, d_str)
    except Exception as e:
        print "Done at %d: %s" % (idx, e)
        break
'''

s.sendall(b"cat << 'EOF' > /tmp/check_upnp2.py\n" + py2_code.encode() + b"\nEOF\n")
time.sleep(1)
s.sendall(b"python /tmp/check_upnp2.py\n")
time.sleep(3)
try:
    out = s.recv(4096).decode('ascii', errors='ignore')
    print(out)
except Exception as e:
    print("Recv err:", e)

s.close()
