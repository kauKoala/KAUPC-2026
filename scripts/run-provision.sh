#!/bin/sh
# A started container is not a completed import. Fail deploy on import or sync errors.
set -eu
docker compose up -d provisioner
container=$(docker compose ps -aq provisioner)
[ -n "$container" ]
code=$(timeout 600 docker wait "$container") || {
  docker compose logs --tail 60 provisioner
  exit 1
}
docker compose logs --tail 30 provisioner
[ "$code" = 0 ] || exit 1
python3 scripts/check-sync.py
