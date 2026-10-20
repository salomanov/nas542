#!/bin/sh
# Step 05: Transmission.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets
require_secrets

TR_DIR=$APPS/transmission

log "Transmission: directories"
mkdir -p "$TR_DIR/downloads" "$TR_DIR/incomplete" "$LOGS" /opt/etc/transmission

log "Transmission: settings"
render "$CONFIGS/transmission/settings.json" /opt/etc/transmission/settings.json
chmod 600 /opt/etc/transmission/settings.json

# the running daemon may hold settings.json
"$INITD/S88transmission" stop >/dev/null 2>&1
sleep 1

log "Transmission: starting"
"$INITD/S88transmission" start >/dev/null 2>&1

# the init script reports "failed" because of a pidof race; wait for the port
n=0
while [ $n -lt 25 ]; do
    netstat -tln 2>/dev/null | grep -q ":5008 " && break
    sleep 1; n=$((n + 1))
done
if ! netstat -tln 2>/dev/null | grep -q ":5008 "; then
    die "transmission did not open port 5008"
fi

# the daemon replaces the plaintext password with a bcrypt hash (may take a moment)
sleep 2
if grep -q '"rpc-password": "\$' /opt/etc/transmission/settings.json 2>/dev/null; then
    log "password stored as a hash"
else
    log "password is still plaintext in the file (daemon hashes it on its own schedule)"
fi

CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
    -u "$TR_USER:$TR_PASS" http://127.0.0.1:5008/transmission/rpc)

case "$CODE" in
    409) log "Transmission ready (RPC 409 = waiting for X-Transmission-Session-Id)" ;;
    401) warn "Transmission: 401 - check rpc-username/rpc-password" ;;
    *)   warn "Transmission: unexpected code $CODE" ;;
esac
echo "  Web UI: http://127.0.0.1:5008/transmission/web/"
