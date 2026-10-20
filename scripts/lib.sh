#!/bin/sh
# Shared helpers for NAS542 scripts.
# Usage:  . "$(cd "$(dirname "$0")" && pwd)/lib.sh"

export PATH=/opt/bin:/opt/sbin:/usr/sbin:/usr/bin:/sbin:/bin

DATA_DIR=${DATA_DIR:-/i-data/45f1aca1}
APPS=${APPS:-$DATA_DIR/Apps}
LOGS=$APPS/logs
INITD=/opt/etc/init.d
PKGCONF=/etc/pkg_service_conf
PKGHTTPD=/i-data/.system/zy-pkgs/pkg_httpd

SELF_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT_DIR=$(cd "$SELF_DIR/.." && pwd)
CONFIGS=$ROOT_DIR/configs

log()  { echo ""; echo "==> $*"; }
warn() { echo "!!! $*" >&2; }
die()  { echo "!!! $*" >&2; exit 1; }

load_secrets() {
    for f in "$SELF_DIR/00-secrets.env" /etc/nas542-secrets.env "$ROOT_DIR/00-secrets.env"; do
        if [ -f "$f" ]; then . "$f"; break; fi
    done
    : "${NAS_ADMIN_USER:=admin}"
    : "${FB_USER:=admin}"
    : "${TR_USER:=admin}"
    : "${ST_USER:=admin}"
    : "${FB_PASS:=}"
    : "${TR_PASS:=}"
    : "${ARIA2_SECRET:=}"
    : "${ST_PASS:=}"
    : "${COPS_USER:=admin}"
    : "${COPS_PASS:=}"
}

require_secrets() {
    [ -n "$FB_PASS" ]      || die "FB_PASS is empty. Fill in scripts/00-secrets.env (see 00-secrets.env.example)."
    [ -n "$TR_PASS" ]      || die "TR_PASS is empty. Fill in scripts/00-secrets.env."
    [ -n "$ARIA2_SECRET" ] || die "ARIA2_SECRET is empty. Fill in scripts/00-secrets.env."
    [ -n "$ST_PASS" ]      || die "ST_PASS is empty. Fill in scripts/00-secrets.env."
    [ -n "$COPS_PASS" ]    || die "COPS_PASS is empty. Fill in scripts/00-secrets.env."
}

# Escape for sed replacement: & | \ must stay literal.
_esc() { printf '%s' "$1" | sed -e 's/[&|\\]/\\&/g'; }

# render <template> <destination>
render() {
    _src=$1; _dst=$2
    sed -e "s|__APPS__|$(_esc "$APPS")|g" \
        -e "s|__DATA__|$(_esc "$DATA_DIR")|g" \
        -e "s|__FB_PASS__|$(_esc "$FB_PASS")|g" \
        -e "s|__TR_PASS__|$(_esc "$TR_PASS")|g" \
        -e "s|__ARIA2_SECRET__|$(_esc "$ARIA2_SECRET")|g" \
        -e "s|__ST_PASS__|$(_esc "$ST_PASS")|g" \
        -e "s|__COPS_USER__|$(_esc "$COPS_USER")|g" \
        -e "s|__COPS_PASS__|$(_esc "$COPS_PASS")|g" \
        "$_src" > "$_dst"

    # Strip a UTF-8 BOM if the template had one: in PHP configs it is printed
    # before headers ("Cannot modify header information").
    if [ -x /opt/bin/python3 ]; then
        /opt/bin/python3 - "$_dst" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
if b.startswith(b'\xef\xbb\xbf'):
    open(p, 'wb').write(b[3:])
PY
    fi
}

install_init() {
    # install_init <file name in configs/init>
    _f="$CONFIGS/init/$1"
    [ -f "$_f" ] || die "missing $_f"
    install -m 755 "$_f" "$INITD/$1"
}

wait_port() {
    # wait_port <port> [seconds]
    _p=$1; _n=${2:-20}
    while [ "$_n" -gt 0 ]; do
        netstat -tln 2>/dev/null | grep -q ":$_p " && return 0
        sleep 1; _n=$((_n - 1))
    done
    return 1
}

http_code() { curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1"; }
