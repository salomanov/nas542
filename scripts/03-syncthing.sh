#!/bin/sh
# Step 03: Syncthing.
SELF=$(cd "$(dirname "$0")" && pwd)
. "$SELF/lib.sh"
load_secrets

ST_HOME=$APPS/syncthing
ST_FOLDER=$APPS/sync
API=http://127.0.0.1:5004

log "Syncthing: directories"
mkdir -p "$ST_HOME" "$ST_FOLDER" "$LOGS" /opt/var/run

log "Syncthing: init script"
install_init S90syncthing
if [ -f "$INITD/S92syncthing" ]; then
    mv "$INITD/S92syncthing" "$INITD/S92syncthing.disabled"
    log "package S92syncthing disabled (conflicts with the old Pulse one)"
fi

# The old Pulse Syncthing holds port 22000 and touches the same folders.
OLD=$(ps w | grep -i '[s]yncthing' | grep -v "$APPS" | awk '{print $1}')
if [ -n "$OLD" ]; then
    warn "foreign syncthing processes found: $OLD"
    warn "if sync does not come up, kill them: kill $OLD"
fi

log "Syncthing: starting"
"$INITD/S90syncthing" restart

log "Syncthing: waiting for API"
n=0
while [ $n -lt 40 ]; do
    if [ -f "$ST_HOME/config.xml" ] && curl -s -o /dev/null "$API/rest/noauth/health"; then
        break
    fi
    sleep 1; n=$((n + 1))
done
[ -f "$ST_HOME/config.xml" ] || die "config.xml was not created - see $LOGS/syncthing.log"

KEY=$(sed -n 's|.*<apikey>\([^<]*\)</apikey>.*|\1|p' "$ST_HOME/config.xml" | head -1)
[ -n "$KEY" ] || die "apikey not found in $ST_HOME/config.xml"

log "Syncthing: GUI login ($ST_USER)"
curl -s -H "X-API-Key: $KEY" "$API/rest/config/gui" > /tmp/st-gui.json
/opt/bin/python3 - "$ST_USER" "$ST_PASS" <<'PY'
import json, sys
d = json.load(open('/tmp/st-gui.json'))
d['address'] = '0.0.0.0:5004'
d['user'] = sys.argv[1]
d['password'] = sys.argv[2]
json.dump(d, open('/tmp/st-gui2.json', 'w'))
PY
GCODE=$(curl -s -o /dev/null -w '%{http_code}' -X PUT \
    -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
    --data-binary @/tmp/st-gui2.json "$API/rest/config/gui")
if [ "$GCODE" = "000" ]; then
    # normal: Syncthing restarts the GUI listener while applying the new settings
    echo "  GUI settings applied (connection reset while restarting the listener)"
else
    echo "  PUT gui: $GCODE"
fi
sleep 2
ACODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 -u "$ST_USER:$ST_PASS" "$API/")
if [ "$ACODE" = "200" ]; then
    echo "  GUI login works"
else
    warn "GUI login check returned $ACODE"
fi

log "Syncthing: folder apps"
MYID=$(curl -s -H "X-API-Key: $KEY" "$API/rest/system/status" \
       | /opt/bin/python3 -c 'import json,sys; print(json.load(sys.stdin)["myID"])' 2>/dev/null)
[ -n "$MYID" ] || die "could not read myID"

if curl -s -H "X-API-Key: $KEY" "$API/rest/config/folders/apps" | grep -q '"id"'; then
    log "folder apps already exists"
else
    curl -s -o /dev/null -w '  PUT folder: %{http_code}\n' -X PUT \
        -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
        -d "{\"id\":\"apps\",\"label\":\"Apps\",\"path\":\"$ST_FOLDER\",\"type\":\"sendreceive\",\"devices\":[{\"deviceID\":\"$MYID\"}]}" \
        "$API/rest/config/folders/apps"
fi

log "Syncthing ready"
echo "  Device ID: $MYID"
echo "  GUI:       $API  (user $ST_USER)"
echo "  Sync port: 22001"
