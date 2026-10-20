#!/bin/sh
# Step 07: COPS (OPDS server for a Calibre library).
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets

COPS_DIR=$APPS/cops
CALIBRE_DIR=$APPS/calibre
DEMO=0
[ "$1" = "--demo" ] && DEMO=1

log "COPS: directories"
mkdir -p "$COPS_DIR" "$CALIBRE_DIR" "$LOGS"

if [ ! -f "$COPS_DIR/index.php" ]; then
    log "COPS: downloading master"
    curl -L --max-time 180 -o /tmp/cops.tar.gz \
        https://github.com/seblucas/cops/archive/refs/heads/master.tar.gz \
        || die "could not download COPS"
    rm -rf /tmp/cops-master
    tar -xzf /tmp/cops.tar.gz -C /tmp || die "could not unpack COPS"
    cp -a /tmp/cops-master/. "$COPS_DIR"/
    rm -rf /tmp/cops-master /tmp/cops.tar.gz
else
    log "COPS: files already present"
fi

log "COPS: composer"
if [ ! -f /tmp/composer.phar ]; then
    curl -L --max-time 120 -o /tmp/composer.phar https://getcomposer.org/composer-stable.phar \
        || die "could not download composer"
fi

# vendor must live on disk: /tmp is a ramdisk
cd "$COPS_DIR" || die "no such directory: $COPS_DIR"
COMPOSER_ALLOW_SUPERUSER=1 COMPOSER_HOME="$APPS/.composer" \
    /opt/bin/php-cli /tmp/composer.phar install --no-dev --no-interaction --no-progress \
    2>&1 | tail -8

[ -f "$COPS_DIR/vendor/autoload.php" ] || die "composer did not produce vendor/"

log "COPS: PHP 8 patch (create_function)"
/opt/bin/python3 - "$COPS_DIR/vendor/seblucas/dot-php/doT.php" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8', errors='surrogateescape').read()
old = "return @create_function ('$it', $func);"
new = "return @eval('return function ($it) { ' . $func . ' };');"
if old in s:
    open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s.replace(old, new))
    print("  patched")
else:
    print("  already patched or pattern not found")
PY

log "COPS: config"
render "$CONFIGS/cops/config_local.php" "$COPS_DIR/config_local.php"

if [ "$DEMO" = "1" ] && [ ! -f "$CALIBRE_DIR/metadata.db" ]; then
    log "COPS: demo library (3 Gutenberg books)"
    /opt/bin/python3 "$SELF/tools/mklib.py" "$CALIBRE_DIR" || warn "mklib.py failed"
fi

log "COPS: starting"
install_init S89cops
"$INITD/S89cops" restart
sleep 2

CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "http://127.0.0.1:5005/feed.php")
if [ "$CODE" = "200" ]; then
    log "COPS ready: OPDS http://127.0.0.1:5005/feed.php"
else
    warn "COPS /feed.php returned HTTP $CODE - see $LOGS/cops.log"
fi
