#!/bin/sh
# Step 10: Deploy yt-dlp Web UI on NAS542
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets

log "ytdl: target directory"
mkdir -p "$APPS/ytdl" "$APPS/ytdl/jobs" "$APPS/downloads/video" "$APPS/logs"

log "ytdl: copying files"
cp -f "$SELF/../apps/ytdl/index.html" "$APPS/ytdl/index.html"
cp -f "$SELF/../apps/ytdl/api.php" "$APPS/ytdl/api.php"
cp -f "$SELF/../apps/ytdl/router.php" "$APPS/ytdl/router.php"

chown -R "$RUNAS:$RUNAS" "$APPS/ytdl" "$APPS/downloads/video"
chmod -R 755 "$APPS/ytdl"

log "ytdl: init script"
install -m 755 "$CONFIGS/init/S89ytdl" /opt/etc/init.d/S89ytdl

log "ytdl: starting service"
/opt/etc/init.d/S89ytdl restart

log "ytdl: proxy rules"
cp -f "$CONFIGS/httpd/apps_proxy.conf" "$PKGCONF/apps_proxy.conf"
/etc/init.d/pkghttpd.sh reload
sleep 2

log "ytdl: check"
code=$(http_code -u "$NAS_ADMIN_USER:$NAS_ADMIN_PASS" "http://127.0.0.1:5000/apps/ytdl/")
echo "  /apps/ytdl/ -> $code"
[ "$code" = "200" ] || warn "ytdl check returned $code"

log "ytdl deployed. Outside: https://<host>:34501/apps/ytdl/"
