#!/bin/sh
# Backup NAS542 configs to /i-data/45f1aca1/Apps/backups/
SELF=$(cd "$(dirname "$0")" && pwd)
. "$(cd "$SELF/.." && pwd)/lib.sh"

B=$APPS/backups
mkdir -p "$B"
F=$B/nas542-$(date +%Y%m%d-%H%M%S).tgz

FILES="
etc/pkg_service_conf/apps_proxy.conf
etc/pkg_service_conf/httpd2.conf
etc/pkg_service_conf/httpd_zld2.conf
opt/etc/init.d/S89cops
opt/etc/init.d/S89ariang
opt/etc/init.d/S90syncthing
opt/etc/filebrowser/filebrowser.conf
opt/etc/transmission/settings.json
opt/etc/aria2.conf
etc/service_conf/CA.cer
"

LIST=""
for f in $FILES; do
    [ -f "/$f" ] && LIST="$LIST /$f"
done
LIST="$LIST $APPS/cops/config_local.php"
[ -f "$APPS/syncthing/config.xml" ] && LIST="$LIST $APPS/syncthing/config.xml"

tar -czf "$F" $LIST 2>/dev/null || die "tar failed"

chmod 600 "$F"
log "Backup: $F ($(du -h "$F" | cut -f1))"
echo "  Files: $(echo $LIST | wc -w)"
echo "  NOTE: config.xml contains the Syncthing API key - keep it private."
