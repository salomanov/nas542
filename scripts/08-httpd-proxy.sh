#!/bin/sh
# Step 08: reverse proxy inside pkg_httpd (mod_proxy).
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets

CONF=$PKGCONF/httpd2.conf
[ -f "$CONF" ] || die "no $CONF - is the PHP-MySQL-phpMyAdmin package installed?"

log "Proxy: rules file"
install -m 644 "$CONFIGS/httpd/apps_proxy.conf" "$PKGCONF/apps_proxy.conf"

log "Proxy: backup of $CONF"
[ -f "$CONF.bak-nas542" ] || cp -p "$CONF" "$CONF.bak-nas542"

log "Proxy: AuthZyxelSkipPattern"
if grep -q "/apps/" "$CONF"; then
    echo "  paths already present"
else
    sed -i '/^AuthZyxelSkipPattern /s|$| /apps/ /transmission/ /jsonrpc|' "$CONF"
    echo "  added /apps/ /transmission/ /jsonrpc"
fi

log "Proxy: include"
if grep -q "apps_proxy.conf" "$CONF"; then
    echo "  include already present"
else
    printf '\n# NAS542: application reverse proxy\nInclude /etc/pkg_service_conf/apps_proxy.conf\n' >> "$CONF"
    echo "  include added"
fi

log "Proxy: config test"
OUT=$(LD_LIBRARY_PATH=/i-data/45f1aca1/.PKG/PHP-MySQL-phpMyAdmin/lib \
      "$PKGHTTPD" -t -f "$CONF" 2>&1)
echo "$OUT" | tail -5
case "$OUT" in
    *"Syntax OK"*) : ;;
    *) die "config test failed - changes NOT applied" ;;
esac

log "Proxy: reloading pkg_httpd"
/etc/init.d/pkghttpd.sh reload
sleep 4

log "Proxy: application checks"
check() {
    code=$(http_code "http://127.0.0.1:5000$1")
    printf '  %-24s %s\n' "$1" "$code"
}
check /apps/sync/
check /apps/cops/
check /apps/aria/
check /apps/fb/
check /apps/cops/feed.php
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
    -X POST -H 'Content-Type: application/json' \
    -d "{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"aria2.getVersion\",\"params\":[\"token:$ARIA2_SECRET\"]}" \
    http://127.0.0.1:5000/jsonrpc)
printf '  %-24s %s\n' "/jsonrpc" "$code"

log "Done. Outside: https://<host>:34501/apps/..."
