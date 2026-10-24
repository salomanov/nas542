import socket
from concurrent.futures import ThreadPoolExecutor

def scan(ip):
    for port in [80, 445, 22, 5001]:
        s = socket.socket()
        s.settimeout(0.3)
        res = s.connect_ex((ip, port))
        s.close()
        if res == 0:
            print("FOUND DEVICE:", ip, "PORT:", port)
            return

ips = [f"192.168.1.{i}" for i in range(1, 255)]
with ThreadPoolExecutor(max_workers=50) as pool:
    pool.map(scan, ips)
print("SCAN_DONE")
