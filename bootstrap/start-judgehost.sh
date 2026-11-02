#!/bin/sh
set -eu

JUDGEDAEMON_PASSWORD=$(awk '$3 == "judgehost" { print $4; exit }' /opt/domjudge/domserver/etc/restapi.secret)
export JUDGEDAEMON_PASSWORD

exec /usr/bin/dumb-init -- /scripts/start.sh
