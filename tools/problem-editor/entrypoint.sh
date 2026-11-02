#!/bin/sh
# 배포 키는 읽기 전용으로 마운트되어 권한이 느슨하다. ssh는 그런 키를 거부하므로 복사해서 쓴다.
set -e
if [ -f /run/secrets/editor_deploy_key ]; then
  mkdir -p /root/.ssh
  cp /run/secrets/editor_deploy_key /root/.ssh/editor_key
  chmod 600 /root/.ssh/editor_key
fi
exec python /app/app.py "${1:-8088}"
