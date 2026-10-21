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

# Test SSDP discovery or port scan on router 192.168.1.1
py_script = '''
import socket, sys

msg = b"""M-SEARCH * HTTP/1.1\\r\\nHOST: 239.255.255.250:1900\\r\\nMAN: \\"ssdp:discover\\"\\r\\nMX: 2\\r\\nST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\\r\\n\\r\\n"""
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(3)
s.sendto(msg, ("239.255.255.250", 1900))
try:
    data, addr = s.recvfrom(2048)
    print("UPnP response from", addr)
    print(data.decode("ascii", errors="ignore"))
except Exception as e:
    print("No UPnP SSDP:", e)
'''

s.sendall(b"python -c '" + py_script.encode() + b"'\n")
time.sleep(3)
try:
    out = s.recv(4096).decode('ascii', errors='ignore')
    print(out)
except Exception as e:
    print("Recv err:", e)

s.close()
