#!/bin/sh
# Step 10: server TLS certificate with SAN.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"

CRT=$ROOT_DIR/tls/leaf_new.crt
KEY=/etc/service_conf/CA_key.cer
DATE=$(date +%Y%m%d)

[ -f "$CRT" ] || die "no $CRT"

log "TLS: current certificate"
if [ -f /etc/service_conf/CA.cer ]; then
    openssl x509 -in /etc/service_conf/CA.cer -noout -subject -dates 2>/dev/null | sed 's/^/  /'
fi

log "TLS: backup"
[ -f /etc/service_conf/CA.cer.bak-$DATE ] || cp -p /etc/service_conf/CA.cer /etc/service_conf/CA.cer.bak-$DATE 2>/dev/null
[ -f /etc/zyxel/cert/CA.cer.bak-$DATE ]   || cp -p /etc/zyxel/cert/CA.cer /etc/zyxel/cert/CA.cer.bak-$DATE 2>/dev/null

log "TLS: installing"
install -m 644 "$CRT" /etc/service_conf/CA.cer
install -m 644 "$CRT" /etc/zyxel/cert/CA.cer

if [ ! -f "$KEY" ]; then
    warn "private key $KEY is missing - certificate installed, but daemons cannot start TLS"
fi

log "TLS: SAN check"
openssl x509 -in /etc/service_conf/CA.cer -noout -subject -dates 2>/dev/null | sed 's/^/  /'
openssl x509 -in /etc/service_conf/CA.cer -noout -text 2>/dev/null \
    | sed -n '/Subject Alternative Name/,+1p' | sed 's/^/  /'

log "TLS: reloading daemons"
/etc/init.d/httpd.sh reload    2>&1 | tail -1
/etc/init.d/davhttpd.sh reload 2>&1 | tail -1
/etc/init.d/pkghttpd.sh reload 2>&1 | tail -1

sleep 3
log "TLS: checks"
echo -n "  https://127.0.0.1:5001 -> "
curl -sk -o /dev/null -w '%{http_code}\n' --max-time 10 https://127.0.0.1:5001/
echo -n "  https://127.0.0.1:443  -> "
curl -sk -o /dev/null -w '%{http_code}\n' --max-time 10 https://127.0.0.1:443/

log "Done"
