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

cmd = r'''
cat << 'EOF' > /tmp/test_propfind.py
import urllib2, base64, re

req = urllib2.Request('http://127.0.0.1:5002/webdav/')
req.get_method = lambda: 'PROPFIND'
req.add_header('Authorization', 'Basic ' + base64.b64encode('admin:12345678'))
req.add_header('Depth', '1')

try:
    resp = urllib2.urlopen(req)
    print "STATUS:", resp.getcode()
    xml = resp.read()
    hrefs = re.findall(r'<[^>]*href[^>]*>(.*?)</[^>]*href[^>]*>', xml)
    print "HREFS_FOUND:"
    for h in hrefs:
        print "  ->", h
except Exception as e:
    print "ERROR:", e
EOF
python /tmp/test_propfind.py
'''
s.sendall(cmd.encode('ascii'))
time.sleep(3)
out = s.recv(4096).decode('utf-8', errors='ignore')
print(out)
s.close()
