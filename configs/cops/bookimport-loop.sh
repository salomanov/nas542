#!/bin/sh
# Watch the Calibre inbox and import new books every 60 seconds.
# Started by /opt/etc/init.d/S91bookimport (runs as admin).
APP=/i-data/45f1aca1/Apps
LOG=$APP/logs/bookimport.log

while :; do
    /opt/bin/python3 "$APP/cops-tools/import_books.py" --quiet >>"$LOG" 2>&1
    sleep 60
done
