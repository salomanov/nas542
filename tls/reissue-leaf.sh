#!/bin/sh
# Re-issue NAS542 leaf cert WITH SAN, signed by the real "Zyxel NAS Root CA".
set -e
cd /tmp
rm -rf newleaf
mkdir -p newleaf
cd newleaf

CA=/tmp/root_ca.crt
CAKEY=/tmp/root_ca.key

echo "== OLD LEAF ==  $(openssl x509 -in /etc/zyxel/cert/CA.cer -noout -subject)"
echo "== OLD LEAF VERIFY vs CA =="
openssl verify -CAfile "$CA" /etc/zyxel/cert/CA.cer || true

cat > ext.cnf <<'EOF'
[srv]
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
subjectAltName = @alt
[alt]
IP.1 = 178.140.8.56
IP.2 = 192.168.1.50
IP.3 = 127.0.0.1
DNS.1 = nas542.local
DNS.2 = nas542
EOF

openssl req -newkey rsa:2048 -sha256 -nodes \
  -keyout server.key -out server.csr \
  -subj "/C=RU/O=Home Network/CN=178.140.8.56" >/dev/null 2>&1

openssl x509 -req -in server.csr -CA "$CA" -CAkey "$CAKEY" \
  -set_serial 0x4E415335 -days 3650 -sha256 \
  -extfile ext.cnf -extensions srv -out server.crt >/dev/null 2>&1

chmod 600 server.key

echo "== NEW CERT =="
openssl x509 -in server.crt -noout -subject -issuer -dates
echo "== SAN =="
openssl x509 -in server.crt -noout -text | grep -A2 "Subject Alternative Name"
echo "== KEY MATCH =="
a=$(openssl rsa -in server.key -noout -modulus | md5sum | cut -d' ' -f1)
b=$(openssl x509 -in server.crt -noout -modulus | md5sum | cut -d' ' -f1)
[ "$a" = "$b" ] && echo "OK" || echo "MISMATCH"
echo "== VERIFY =="
openssl verify -CAfile "$CA" server.crt
