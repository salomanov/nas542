#!/bin/sh
# Step 02: opkg packages.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"

PKGS="
syncthing
filebrowser
transmission-daemon
transmission-web
aria2
yt-dlp
ffmpeg
curl
ca-certificates
unzip
git
git-http
python3
python3-pillow
python3-lxml
python3-requests
python3-dateutil
php8-cli
php8-mod-filter
php8-mod-intl
php8-mod-openssl
php8-mod-xml
php8-mod-ctype
php8-mod-sqlite3
php8-mod-pdo-sqlite
php8-mod-dom
php8-mod-simplexml
php8-mod-mbstring
php8-mod-gd
php8-mod-fileinfo
php8-mod-session
php8-mod-iconv
php8-mod-curl
php8-mod-phar
php8-mod-xmlwriter
php8-mod-zip
"

wait_opkg() {
    n=0
    while ps w 2>/dev/null | grep -v grep | grep -q opkg; do
        n=$((n + 1))
        [ "$n" -gt 900 ] && die "opkg has been busy for more than 15 minutes"
        [ $((n % 15)) -eq 0 ] && log "waiting for opkg lock (${n}s)"
        sleep 1
    done
}

log "opkg update"
wait_opkg
/opt/bin/opkg update 2>&1 | tail -3

log "Installing packages (may take 10-20 minutes)"
wait_opkg
/opt/bin/opkg install $PKGS 2>&1 | tail -25

log "Checking binaries"
for b in /opt/bin/syncthing /opt/bin/filebrowser /opt/bin/transmission-daemon \
         /opt/bin/aria2c /opt/bin/php-cli /opt/bin/curl /opt/bin/git; do
    if [ -x "$b" ]; then echo "  ok   $b"; else warn "MISSING $b"; fi
done

log "PHP modules"
/opt/bin/php-cli -m | tr '\n' ' ' | head -c 500
echo ""

[ -x /opt/bin/php-cli ] || die "php-cli was not installed"
log "Packages ready"
