#!/bin/sh
# Step 01: verify Entware.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"

log "Checking Entware"

[ -x /opt/bin/opkg ] || die "Entware not found (/opt/bin/opkg).
Install the Entware-ng package via the NAS web UI (App Center), then run this again."

if [ -L /opt ]; then
    log "/opt -> $(readlink /opt)"
fi

log "opkg: $(/opt/bin/opkg --version 2>&1 | head -1)"

if ! grep -q '/opt/bin' /etc/profile 2>/dev/null; then
    warn "/opt/bin is not in /etc/profile (not critical: scripts use absolute paths)"
fi

log "Entware OK"
