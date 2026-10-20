#!/bin/sh
# Step 04: FileBrowser.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets
require_secrets

FB_DIR=$APPS/filebrowser
DB=$FB_DIR/filebrowser.db

log "FileBrowser: directories"
mkdir -p "$FB_DIR" "$LOGS"

log "FileBrowser: config"
install -d /opt/etc/filebrowser
render "$CONFIGS/filebrowser/filebrowser.conf" /opt/etc/filebrowser/filebrowser.conf
chmod 600 /opt/etc/filebrowser/filebrowser.conf

# CLI operations fail while the daemon holds the Bolt DB
"$INITD/S99filebrowser" stop >/dev/null 2>&1
sleep 1

if [ ! -f "$DB" ]; then
    log "FileBrowser: creating database"
    /opt/bin/filebrowser -d "$DB" config init >/dev/null 2>&1 || die "config init failed"

    log "FileBrowser: user $FB_USER"
    HASH=$(/opt/bin/php-cli -r 'echo password_hash($argv[1], PASSWORD_BCRYPT);' -- "$FB_PASS" \
           | sed 's/^\$2y\$/\$2a$/')
    [ -n "$HASH" ] || die "could not compute bcrypt hash"

    cat > /tmp/fb-user.json <<EOF
[{"username":"$FB_USER","password":"$HASH","perm":{"admin":true,"execute":true,"create":true,"rename":true,"modify":true,"delete":true,"share":true,"download":true}}]
EOF
    /opt/bin/filebrowser -d "$DB" users import /tmp/fb-user.json || die "users import failed"
else
    log "FileBrowser: database exists, keeping the user"
fi

log "FileBrowser: starting"
"$INITD/S99filebrowser" start
n=0
while [ $n -lt 15 ]; do
    netstat -tln 2>/dev/null | grep -q ":5007 " && break
    sleep 1; n=$((n + 1))
done

CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
    -X POST -H 'Content-Type: application/json' \
    -d "{\"username\":\"$FB_USER\",\"password\":\"$FB_PASS\"}" \
    http://127.0.0.1:5007/api/login)

if [ "$CODE" = "200" ]; then
    log "FileBrowser ready (http://127.0.0.1:5007, baseurl /apps/fb)"
else
    warn "login returned HTTP $CODE - check $LOGS/filebrowser.log"
fi
