#!/bin/sh
# Step 06: aria2 + AriaNg.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets
require_secrets

AR_DIR=$APPS/aria2
NG_DIR=$APPS/ariang
ARIA2_VER=1.3.15

log "aria2: directories"
mkdir -p "$AR_DIR/downloads" "$NG_DIR" /opt/var/aria2 /opt/var/log "$LOGS"

log "aria2: config"
render "$CONFIGS/aria2/aria2.conf" /opt/etc/aria2.conf
chmod 600 /opt/etc/aria2.conf

"$INITD/S81aria2" restart >/dev/null 2>&1
sleep 3

CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST \
    -H 'Content-Type: application/json' \
    -d "{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"aria2.getVersion\",\"params\":[\"token:$ARIA2_SECRET\"]}" \
    http://127.0.0.1:6800/jsonrpc)

if [ "$CODE" = "200" ]; then
    log "aria2 ready (RPC 6800)"
else
    warn "aria2 RPC returned HTTP $CODE - see /opt/var/log/aria2.log"
fi

# --- AriaNg ---
if [ ! -f "$NG_DIR/index.html" ]; then
    log "AriaNg: downloading $ARIA2_VER"
    curl -L --max-time 120 -o /tmp/ariang.zip \
        "https://github.com/mayswind/AriaNg/releases/download/$ARIA2_VER/AriaNg-$ARIA2_VER.zip" \
        || die "could not download AriaNg"
    unzip -o -q /tmp/ariang.zip -d "$NG_DIR" || die "could not unpack AriaNg"
    rm -f /tmp/ariang.zip
else
    log "AriaNg already installed"
fi

log "AriaNg: router and init"
install -m 644 "$CONFIGS/ariang/router.php" "$NG_DIR/router.php"
install_init S89ariang
"$INITD/S89ariang" restart

sleep 2
CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 http://127.0.0.1:5006/)
if [ "$CODE" = "200" ]; then
    log "AriaNg ready (http://127.0.0.1:5006, baseurl /apps/aria)"
else
    warn "AriaNg returned HTTP $CODE"
fi
echo "  RPC for AriaNg: https://<host>:34501/jsonrpc, secret from 00-secrets.env"
