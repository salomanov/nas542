import socket

for host in ['192.168.1.50', '178.140.8.56']:
    print("Testing host:", host)
    for port in [23, 22, 80, 445, 5001, 5003, 34501, 34523]:
        s = socket.socket()
        s.settimeout(1.5)
        res = s.connect_ex((host, port))
        s.close()
        status = "OPEN" if res == 0 else "CLOSED (%d)" % res
        print("  %s:%d -> %s" % (host, port, status))
