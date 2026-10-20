#!/bin/sh
# Health check for all NAS542 services.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$(cd "$SELF/.." && pwd)/lib.sh"
load_secrets

OK=0
BAD=0

ok()  { OK=$((OK + 1));  printf '  [ OK ] %s\n' "$*"; }
bad() { BAD=$((BAD + 1)); printf '  [FAIL] %s\n' "$*"; }
say() { echo ""; echo "--- $* ---"; }

say "Ports"
for p in 5000 5001 5004 5005 5006 5007 5008 6800; do
    if netstat -tln 2>/dev/null | grep -q ":$p "; then
        ok "port $p is listening"
    else
        bad "port $p is not listening"
    fi
done

say "HTTP (local)"
check_code() {
    c=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 "$1")
    case "|$2|" in
        *"|$c|"*) ok "$1 -> $c" ;;
        *)        bad "$1 -> $c (expected $2)" ;;
    esac
}
check_code_auth() {
    c=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 -u "$COPS_USER:$COPS_PASS" "$1")
    case "|$2|" in
        *"|$c|"*) ok "$1 -> $c (auth)" ;;
        *)        bad "$1 -> $c (expected $2 with auth)" ;;
    esac
}
check_code "https://127.0.0.1:5001/pkg/ownCloud/status.php" "200"
check_code "http://127.0.0.1:5004/" "200|401"
check_code "http://127.0.0.1:5005/feed.php" "401"
check_code_auth "http://127.0.0.1:5005/feed.php" "200"
check_code "http://127.0.0.1:5006/" "200"
check_code "http://127.0.0.1:5007/" "200|302"
check_code "http://127.0.0.1:5008/transmission/web/" "200|401"

say "Through pkg_httpd proxy (5001)"
check_code "https://127.0.0.1:5001/apps/sync/" "200|401"
check_code "https://127.0.0.1:5001/apps/cops/feed.php" "401"
check_code_auth "https://127.0.0.1:5001/apps/cops/feed.php" "200"
check_code "https://127.0.0.1:5001/apps/aria/" "200"
check_code "https://127.0.0.1:5001/apps/fb/" "200|302"

say "aria2 RPC"
if [ -n "$ARIA2_SECRET" ]; then
    R=$(curl -s --max-time 10 -X POST -H 'Content-Type: application/json' \
        -d "{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"aria2.getVersion\",\"params\":[\"token:$ARIA2_SECRET\"]}" \
        http://127.0.0.1:6800/jsonrpc)
    case "$R" in
        *'"version"'*) ok "aria2 answers directly" ;;
        *)             bad "aria2 direct: $(echo "$R" | head -c 120)" ;;
    esac
    R=$(curl -sk --max-time 10 -X POST -H 'Content-Type: application/json' \
        -d "{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"aria2.getVersion\",\"params\":[\"token:$ARIA2_SECRET\"]}" \
        https://127.0.0.1:5001/jsonrpc)
    case "$R" in
        *'"version"'*) ok "aria2 through /jsonrpc proxy" ;;
        *)             bad "aria2 proxy: $(echo "$R" | head -c 120)" ;;
    esac
fi

say "Transmission RPC"
if [ -n "$TR_PASS" ]; then
    c=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
        -u "$TR_USER:$TR_PASS" http://127.0.0.1:5008/transmission/rpc)
    case "$c" in
        409|200) ok "Transmission RPC -> $c" ;;
        *)       bad "Transmission RPC -> $c" ;;
    esac
fi

say "Syncthing"
CFG=$APPS/syncthing/config.xml
if [ -f "$CFG" ]; then
    KEY=$(sed -n 's|.*<apikey>\([^<]*\)</apikey>.*|\1|p' "$CFG" | head -1)
    R=$(curl -s --max-time 10 -H "X-API-Key: $KEY" http://127.0.0.1:5004/rest/system/status)
    MYID=$(echo "$R" | /opt/bin/python3 -c 'import json,sys; print(json.load(sys.stdin)["myID"])' 2>/dev/null)
    if [ -n "$MYID" ]; then
        ok "Syncthing is up, Device ID: $MYID"
    else
        bad "Syncthing REST does not answer"
    fi
else
    bad "no $CFG"
fi

say "OPDS"
F=$(curl -sk --max-time 15 -u "$COPS_USER:$COPS_PASS" https://127.0.0.1:5001/apps/cops/feed.php)
case "$F" in
    *"<feed"*) ok "OPDS feed is served ($(echo "$F" | grep -c '<entry>') entries)" ;;
    *)         bad "OPDS feed is not available" ;;
esac

say "Memory"
free -m | head -2 | sed 's/^/  /'

echo ""
echo "Total: OK=$OK, FAIL=$BAD"
[ "$BAD" -eq 0 ]
