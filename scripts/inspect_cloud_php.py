import socket

class TelnetClient:
    def __init__(self, host='178.140.8.56', port=34523):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(15)
        self.s.connect((host, port))
        self.read_until(b'login: ')
        self.s.sendall(b'admin\n')
        self.read_until(b'Password: ')
        self.s.sendall(b'12345678\n')
        self.read_until(b'$ ')
        self.s.sendall(b'/bin/busybox su\n')
        self.read_until(b'Password: ')
        self.s.sendall(b'12345678\n')
        self.read_until(b'# ')

    def read_until(self, expected):
        buf = b''
        while expected not in buf:
            chunk = self.s.recv(1024)
            if not chunk:
                break
            buf += chunk
        return buf

    def cmd(self, command):
        self.s.sendall(command.encode('utf-8') + b'\n')
        res = self.read_until(b'# ')
        return res.decode('utf-8', errors='ignore')

    def close(self):
        self.s.close()

tc = TelnetClient()
print("CHECKING IF files_sharing has capabilities.php anywhere:")
print(tc.cmd('find /i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud/apps/files_sharing -name "*capab*"'))
tc.close()
