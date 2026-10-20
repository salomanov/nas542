#!/bin/sh
# Full install: run every step in order.
# Usage:  sh install-all.sh [--skip-tls]
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets
require_secrets

SKIP_TLS=0
[ "$1" = "--skip-tls" ] && SKIP_TLS=1

STEPS="01-entware.sh 02-packages.sh 03-syncthing.sh 04-filebrowser.sh 05-transmission.sh 06-aria2-ariang.sh 07-cops.sh 08-httpd-proxy.sh 09-owncloud-shims.sh"
[ "$SKIP_TLS" = "1" ] || STEPS="$STEPS 10-tls.sh"

FAILED=""

for s in $STEPS; do
    log "########## $s ##########"
    if sh "$SELF/$s"; then
        :
    else
        warn "step $s failed"
        FAILED="$FAILED $s"
    fi
done

log "########## healthcheck ##########"
sh "$SELF/tools/healthcheck.sh"

echo ""
if [ -n "$FAILED" ]; then
    warn "Finished with failed steps:$FAILED"
    exit 1
fi
log "Install complete"
