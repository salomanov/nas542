#!/bin/sh
# Step 07: COPS (OPDS server for a Calibre library) + theme + book importer.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets
require_secrets

COPS_DIR=$APPS/cops
CALIBRE_DIR=$APPS/calibre
TOOLS_DIR=$APPS/cops-tools
THEME=$COPS_DIR/templates/nas542
DEMO=0
[ "$1" = "--demo" ] && DEMO=1

log "COPS: directories"
mkdir -p "$COPS_DIR" "$CALIBRE_DIR/inbox" "$CALIBRE_DIR/.thumbs" "$TOOLS_DIR" "$LOGS"
# The importer runs as admin: it must be able to write into the library and the log.
chown -R admin:root "$CALIBRE_DIR" "$TOOLS_DIR" 2>/dev/null
chown admin:root "$LOGS" 2>/dev/null
chown admin:root "$LOGS"/*.log 2>/dev/null

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
if [ ! -f "$COPS_DIR/vendor/autoload.php" ]; then
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
else
    log "  vendor/ already present"
fi

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

# ---------------------------------------------------------------- theme
log "COPS: theme nas542"
if [ ! -d "$THEME" ]; then
    cp -a "$COPS_DIR/templates/bootstrap" "$THEME"
    echo "  copied from bootstrap"
fi

install -m 644 "$CONFIGS/cops/theme/header.html" "$THEME/header.html"
install -m 644 "$CONFIGS/cops/theme/custom.css" "$THEME/styles/custom.css"

# file.html: load our CSS and our copy of cops.js (idempotent)
/opt/bin/python3 - "$THEME/file.html" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
s = s.replace('templates/bootstrap/scripts/cops.js', 'templates/nas542/scripts/cops.js')
if 'styles/custom.css' not in s:
    s = s.replace('</head>', '    <link rel="stylesheet" href="templates/nas542/styles/custom.css" />\n</head>')
    print("  file.html patched")
open(p, 'w', encoding='utf-8').write(s)
PY

log "COPS: icons"
if [ ! -f "$COPS_DIR/images/favicon.ico" ] || [ ! -f "$COPS_DIR/images/nas542-logo.png" ]; then
    /opt/bin/python3 "$CONFIGS/cops/theme/make_icon.py" "$COPS_DIR/images" || warn "icon generation failed"
else
    echo "  icons already present"
fi

# ---------------------------------------------------------------- modern UI
log "COPS: modern interface"
mkdir -p "$COPS_DIR/ui/assets"
install -m 644 "$CONFIGS/cops/ui/index.php" "$COPS_DIR/ui/index.php"
install -m 644 "$CONFIGS/cops/ui/api.php" "$COPS_DIR/ui/api.php"
install -m 644 "$CONFIGS/cops/ui/assets/app.css" "$COPS_DIR/ui/assets/app.css"
install -m 644 "$CONFIGS/cops/ui/assets/app.js" "$COPS_DIR/ui/assets/app.js"
chown -R admin:root "$COPS_DIR/ui"

# Plain /apps/cops/ opens the new interface; OPDS and deep links keep working.
/opt/bin/python3 - "$COPS_DIR/index.php" <<'PY'
import sys
path = sys.argv[1]
src = open(path, encoding='utf-8', errors='surrogateescape').read()
if 'NAS542: modern catalogue' in src:
    print('  index.php already patched')
else:
    needle = "    require_once dirname(__FILE__) . '/base.php';"
    insert = (
        needle + "\n\n"
        "    // NAS542: modern catalogue is the default entry point.\n"
        "    if (!isset($_GET['page']) && !isset($_GET['query']) && !isset($_GET['id']) && !isset($_GET['db'])) {\n"
        "        header('Location: ui/');\n"
        "        exit();\n"
        "    }"
    )
    if needle in src:
        open(path, 'w', encoding='utf-8', errors='surrogateescape').write(src.replace(needle, insert, 1))
        print('  index.php patched')
    else:
        print('  pattern not found, skipped')
PY

# ---------------------------------------------------------------- importer
log "COPS: book importer"
install -m 755 "$SELF/tools/import_books.py" "$TOOLS_DIR/import_books.py"
install -m 755 "$CONFIGS/cops/bookimport-loop.sh" "$TOOLS_DIR/bookimport-loop.sh"
install_init S91bookimport

if [ "$DEMO" = "1" ] && [ ! -f "$CALIBRE_DIR/metadata.db" ]; then
    log "COPS: demo library (3 Gutenberg books)"
    /opt/bin/python3 "$SELF/tools/mklib.py" "$CALIBRE_DIR" || warn "mklib.py failed"
fi

log "COPS: starting"
install_init S89cops
"$INITD/S89cops" restart
"$INITD/S91bookimport" restart
sleep 2

CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "http://127.0.0.1:5005/feed.php")
CODE_AUTH=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -u "$COPS_USER:$COPS_PASS" \
    "http://127.0.0.1:5005/feed.php")
if [ "$CODE" = "401" ] && [ "$CODE_AUTH" = "200" ]; then
    log "COPS ready: OPDS http://127.0.0.1:5005/feed.php (basic auth: $COPS_USER)"
elif [ "$CODE" = "200" ]; then
    warn "COPS answers without a password - basic auth is NOT active"
else
    warn "COPS check: no auth -> $CODE, with auth -> $CODE_AUTH"
fi

UI=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -u "$COPS_USER:$COPS_PASS" "http://127.0.0.1:5005/ui/")
UI_NOAUTH=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "http://127.0.0.1:5005/ui/")
API_BOOKS=$(curl -s --max-time 20 -u "$COPS_USER:$COPS_PASS" \
    "http://127.0.0.1:5005/ui/api.php?action=list&limit=1" | head -c 60)
echo "  UI:  /ui/ -> $UI (without password: $UI_NOAUTH)"
echo "  API: $API_BOOKS"
echo "  Old interface: /apps/cops/index.php?page=1, settings: ?page=19"
echo "  Inbox:  $CALIBRE_DIR/inbox (drop epub/fb2 here)"
echo "  Import: /opt/etc/init.d/S91bookimport status"
