#!/bin/sh
# Generate a private CA + server certificate with proper SAN for NAS542
set -e
cd /tmp
rm -rf nascert
mkdir -p nascert
cd nascert

cat > openssl.cnf <<'EOF'
[req]
distinguished_name = dn
prompt = no
[dn]
C = RU
O = Home Lab
CN = NAS542
[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
[server]
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
subjectAltName = @alt
[alt]
IP.1 = 178.140.8.56
IP.2 = 192.168.1.50
DNS.1 = nas542.local
DNS.2 = nas542
EOF

# 1) Root CA (10 years)
openssl req -x509 -newkey rsa:2048 -sha256 -nodes \
  -keyout root.key -out root.crt -days 3650 \
  -config openssl.cnf -extensions v3_ca \
  -subj "/C=RU/O=Home Lab/CN=NAS542 Home Root CA" >/dev/null 2>&1

# 2) Server key + CSR
openssl req -newkey rsa:2048 -sha256 -nodes \
  -keyout server.key -out server.csr \
  -config openssl.cnf -subj "/C=RU/O=Home Lab/CN=nas542" >/dev/null 2>&1

# 3) Sign with our CA (10 years)
openssl x509 -req -in server.csr -CA root.crt -CAkey root.key -CAcreateserial \
  -out server.crt -days 3650 -sha256 \
  -extfile openssl.cnf -extensions server >/dev/null 2>&1

chmod 600 root.key server.key
echo "== ROOT =="
openssl x509 -in root.crt -noout -subject -issuer -dates
echo "== SERVER =="
openssl x509 -in server.crt -noout -subject -issuer -dates
echo "== SAN =="
openssl x509 -in server.crt -noout -text | grep -A2 "Subject Alternative Name"
echo "== VERIFY =="
openssl verify -CAfile root.crt server.crt
