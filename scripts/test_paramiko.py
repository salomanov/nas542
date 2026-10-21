import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(
    '178.140.8.56',
    port=34522,
    username='admin',
    password='12345678',
    timeout=10,
    disabled_algorithms=dict(pubkeys=[])
)

stdin, stdout, stderr = ssh.exec_command("echo 'SSH_OK'; python -c \"import sys; print(sys.version)\"")
print(stdout.read().decode('utf-8'))
ssh.close()
