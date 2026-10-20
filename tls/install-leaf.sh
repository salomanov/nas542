#!/bin/sh
# Final leaf: SAN + signed by root CA, reusing the key already installed on the NAS.
set -e
cd /tmp
rm -rf leaf2
mkdir -p leaf2
cd leaf2

CA=/tmp/root_ca.crt
CAKEY=/tmp/root_ca.key
SRVKEY=/etc/zyxel/cert/key/CA_key.cer

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

openssl req -new -key "$SRVKEY" -out server.csr \
  -subj "/C=RU/O=Home Network/CN=178.140.8.56" >/dev/null 2>&1

openssl x509 -req -in server.csr -CA "$CA" -CAkey "$CAKEY" \
  -set_serial 0x4E415336 -days 3650 -sha256 \
  -extfile ext.cnf -extensions srv -out server.crt >/dev/null 2>&1

echo "== NEW CERT =="
openssl x509 -in server.crt -noout -subject -issuer -dates
echo "== SAN =="
openssl x509 -in server.crt -noout -text | grep -A2 "Subject Alternative Name"
echo "== KEY MATCH (must equal installed server key) =="
a=$(openssl rsa -in "$SRVKEY" -noout -modulus | md5sum | cut -d' ' -f1)
b=$(openssl x509 -in server.crt -noout -modulus | md5sum | cut -d' ' -f1)
[ "$a" = "$b" ] && echo "OK: matches installed key" || { echo "MISMATCH - abort"; exit 1; }
echo "== VERIFY =="
openssl verify -CAfile "$CA" server.crt

# ---- install with backups ----
STAMP=20261020
for f in /etc/service_conf/CA.cer /etc/zyxel/cert/CA.cer; do
  [ -f "$f.bak-$STAMP" ] || cp -p "$f" "$f.bak-$STAMP"
done
[ -f /etc/service_conf/CA_key.cer.bak-$STAMP ] || cp -p /etc/service_conf/CA_key.cer /etc/service_conf/CA_key.cer.bak-$STAMP

cp server.crt /etc/service_conf/CA.cer
cp server.crt /etc/zyxel/cert/CA.cer
chmod 644 /etc/service_conf/CA.cer /etc/zyxel/cert/CA.cer
chmod 600 /etc/service_conf/CA_key.cer /etc/zyxel/cert/key/CA_key.cer

echo "== INSTALLED =="
openssl x509 -in /etc/service_conf/CA.cer -noout -subject -dates
