#!/bin/sh
# Step 09: ownCloud 7 compatibility shims (OC10 DAV).
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"

OCROOT=/i-data/45f1aca1/.PKG/ownCloud/gui/ownCloud
RP=$OCROOT/remote.php
PHP5=/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/php/bin/php

[ -d "$OCROOT" ] || die "ownCloud is not installed: no $OCROOT"
[ -f "$RP" ]     || die "no such file: $RP"

log "ownCloud: backup of remote.php"
[ -f "$RP.bak-davshim" ] || cp -p "$RP" "$RP.bak-davshim"

log "ownCloud: OC10-DAV-SHIM block"
if grep -q "OC10-DAV-SHIM" "$RP"; then
    echo "  shim already present"
else
    LINE=$(grep -n "require_once 'lib/base.php';" "$RP.bak-davshim" | head -1 | cut -d: -f1)
    [ -n "$LINE" ] || die "anchor require_once 'lib/base.php' not found in remote.php"
    {
        head -n "$LINE" "$RP.bak-davshim"
        cat "$CONFIGS/owncloud/dav-shim.block"
        tail -n +$((LINE + 1)) "$RP.bak-davshim"
    } > "$RP.new"
    cat "$RP.new" > "$RP"
    rm -f "$RP.new"
    echo "  inserted after line $LINE"
fi

log "ownCloud: dav-uploads-shim.php"
install -m 644 "$CONFIGS/owncloud/dav-uploads-shim.php" "$OCROOT/dav-uploads-shim.php"

log "ownCloud: ocs/v2.php"
if [ ! -f "$OCROOT/ocs/v2.php" ]; then
    cp -p "$OCROOT/ocs/v1.php" "$OCROOT/ocs/v2.php"
    echo "  created from v1.php"
else
    echo "  already present"
fi

log "ownCloud: permissions"
chown nobody:nogroup "$RP" "$OCROOT/dav-uploads-shim.php" "$OCROOT/ocs/v2.php" 2>/dev/null
chmod 644 "$RP" "$OCROOT/dav-uploads-shim.php" "$OCROOT/ocs/v2.php"

log "ownCloud: syntax check"
if [ -x "$PHP5" ]; then
    OUT=$("$PHP5" -l "$RP" 2>&1)
    case "$OUT" in
        *"shared libraries"*|*"not found"*)
            # the bundled php5 CLI needs libmcrypt, which is not installed;
            # this does not affect mod_php5 inside pkg_httpd
            warn "php5 CLI cannot start (missing libs), skipping the syntax check"
            ;;
        *"No syntax errors"*)
            echo "  syntax OK"
            ;;
        *)
            echo "$OUT"
            die "syntax error in remote.php - restore from $RP.bak-davshim"
            ;;
    esac
else
    warn "php5 CLI not found, skipping the check"
fi

log "ownCloud: status"
CODE=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 \
    https://127.0.0.1:5001/pkg/ownCloud/status.php)
echo "  status.php -> $CODE"

log "Shims installed"
echo "  Rollback: cp -p $RP.bak-davshim $RP && rm -f $OCROOT/dav-uploads-shim.php $OCROOT/ocs/v2.php"
