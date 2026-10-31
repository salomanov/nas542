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

# Python script to query UPnP port mappings from MiniUPnPd
py_script = '''
import urllib.request, re

desc = urllib.request.urlopen("http://192.168.1.1:1900/rootDesc.xml", timeout=5).read().decode("utf-8")
print("Desc read, length:", len(desc))

control_url = None
m = re.search(r"<serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>.*?<controlURL>(.*?)</controlURL>", desc, re.S)
if m:
    control_url = m.group(1)
else:
    m = re.search(r"<serviceType>urn:schemas-upnp-org:service:WANPPPConnection:1</serviceType>.*?<controlURL>(.*?)</controlURL>", desc, re.S)
    if m:
        control_url = m.group(1)

if not control_url.startswith("/"):
    control_url = "/" + control_url

full_url = "http://192.168.1.1:1900" + control_url
print("Control URL:", full_url)

# Query port mapping list
for idx in range(30):
    body = f"""<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:GetGenericPortMappingEntry xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
<NewPortMappingIndex>{idx}</NewPortMappingIndex>
</u:GetGenericPortMappingEntry>
</s:Body>
</s:Envelope>"""
    req = urllib.request.Request(full_url, data=body.encode("utf-8"), headers={
        "SOAPAction": '"urn:schemas-upnp-org:service:WANIPConnection:1#GetGenericPortMappingEntry"',
        "Content-Type": 'text/xml; charset="utf-8"'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=3).read().decode("utf-8")
        ext_port = re.search(r"<NewExternalPort>(\d+)</NewExternalPort>", resp)
        int_port = re.search(r"<NewInternalPort>(\d+)</NewInternalPort>", resp)
        proto = re.search(r"<NewProtocol>(.*?)</NewProtocol>", resp)
        client = re.search(r"<NewInternalClient>(.*?)</NewInternalClient>", resp)
        desc_p = re.search(r"<NewPortMappingDescription>(.*?)</NewPortMappingDescription>", resp)
        print(f"[{idx}] {proto.group(1) if proto else ''} WAN:{ext_port.group(1) if ext_port else ''} -> {client.group(1) if client else ''}:{int_port.group(1) if int_port else ''} ({desc_p.group(1) if desc_p else ''})")
    except Exception as e:
        print(f"Done at index {idx}: {e}")
        break
'''

# save script to file on NAS and execute
s.sendall(b"cat << 'EOF' > /tmp/query_upnp.py\n" + py_script.encode() + b"\nEOF\n")
time.sleep(1)
s.sendall(b"python /tmp/query_upnp.py\n")
time.sleep(3)
try:
    out = s.recv(4096).decode('ascii', errors='ignore')
    print(out)
except Exception as e:
    print("Recv err:", e)

s.close()
