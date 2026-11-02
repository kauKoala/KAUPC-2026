#!/usr/bin/env bash
# EC2(Ubuntu)에 DOMjudge 스택을 올린다. 한 번만 실행하면 되고, 다시 실행해도 안전하다.
#
#   bash setup.sh                      # 기본: 저장소를 ~/oj-domjudge에 클론
#   REPO_BRANCH=master bash setup.sh   # 다른 브랜치를 쓰고 싶을 때
set -euo pipefail

REPO_URL="${REPO_URL:-git@github.com:kauKoala/KAUPC-2026.git}"
REPO_DIR="${REPO_DIR:-$HOME/oj-domjudge}"
REPO_BRANCH="${REPO_BRANCH:-master}"

echo "== 1/5 도커 설치"
if ! command -v docker >/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq ca-certificates curl git
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -qq
  sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER"
else
  echo "   이미 설치되어 있다"
fi

echo "== 2/5 저장소 준비"
# 에디터 컨테이너가 root로 커밋하므로 .git 객체 주인이 섞인다. 매번 맞춰 준다.
if [ -d "$REPO_DIR" ]; then
  sudo chown -R "$USER":"$USER" "$REPO_DIR"
fi
git config --global --add safe.directory "$REPO_DIR" 2>/dev/null || true
# 비공개 저장소라 배포 키로 받는다.
if [ -f "$HOME/editor_deploy_key" ]; then
  install -m 600 "$HOME/editor_deploy_key" "$HOME/.ssh_deploy_key"
  export GIT_SSH_COMMAND="ssh -i $HOME/.ssh_deploy_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
fi
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" fetch --quiet origin
  git -C "$REPO_DIR" checkout --quiet "$REPO_BRANCH"
  # 문제 에디터가 서버에서 만든 커밋이 아직 원격에 없을 수 있다. 버리지 않고 원격 위로 올린다.
  # 에디터가 파일을 쓰는 도중이면 받기가 실패할 수 있어 5초 간격으로 세 번까지 다시 받는다.
  pulled=
  for attempt in 1 2 3; do
    if git -C "$REPO_DIR" -c user.name="kaupc deploy" -c user.email=deploy@localhost \
        pull --quiet --rebase --autostash origin "$REPO_BRANCH"; then
      pulled=1
      break
    fi
    git -C "$REPO_DIR" rebase --abort 2>/dev/null || true
    if [ "$attempt" -lt 3 ]; then sleep 5; fi
  done
  if [ -z "$pulled" ]; then
    echo "문제 에디터 커밋과 원격이 충돌한다. 서버에서 직접 풀어야 한다." >&2
    exit 1
  fi
  if [ -n "$(git -C "$REPO_DIR" log --oneline "origin/$REPO_BRANCH..HEAD")" ]; then
    git -C "$REPO_DIR" push --quiet origin "HEAD:$REPO_BRANCH"
  fi
else
  git clone --quiet --branch "$REPO_BRANCH" "$REPO_URL" "$REPO_DIR"
fi

echo "== 3/5 비밀 파일 확인"
mkdir -p "$REPO_DIR/secrets"
for file in "$HOME/.env" "$HOME/editor_deploy_key"; do
  [ -f "$file" ] || continue
  case "$file" in
    *.env) cp "$file" "$REPO_DIR/.env" ;;
    *) cp "$file" "$REPO_DIR/secrets/editor_deploy_key"; chmod 600 "$REPO_DIR/secrets/editor_deploy_key" ;;
  esac
done
if [ ! -f "$REPO_DIR/secrets/editor_deploy_key" ]; then
  echo "   배포 키가 없다. 웹 에디터는 커밋만 하고 푸시는 건너뛴다"
  : > "$REPO_DIR/secrets/editor_deploy_key"
  chmod 600 "$REPO_DIR/secrets/editor_deploy_key"
fi

echo "== 4/5 스택 기동"
cd "$REPO_DIR"
# override 파일로 두면 compose가 항상 자동으로 읽는다.
# 이렇게 해야 "docker compose up -d <서비스>"처럼 부분 명령을 써도 포트 설정이 유지된다.
if [ -f docker-compose.cloud.yml ]; then
  cp docker-compose.cloud.yml docker-compose.override.yml
fi
sudo docker compose up -d --build
# custom/nginx는 디렉터리째 마운트돼 파일은 바로 바뀌지만 nginx는 다시 읽어야 쓴다.
# domserver를 재시작하지 않고 설정만 다시 읽혀 채점 중인 제출과 로그인 세션을 그대로 둔다.
sudo docker compose exec -T domserver sh -c 'nginx -t && nginx -s reload'
sudo bash scripts/run-provision.sh
# 빌드 캐시와 옛 에디터 이미지가 쌓이면 디스크가 1GB 아래로 내려가 채점기가 멈춘다. 빌드할 때마다 비운다.
sudo docker builder prune -af >/dev/null
sudo docker image prune -f >/dev/null
# Caddyfile은 파일 단위로 마운트돼 git pull 뒤에도 옛 내용이 보인다. 다시 띄워 새 설정을 읽힌다.
if sudo docker compose ps --services | grep -qx caddy; then
  sudo docker compose restart caddy
fi

echo "== 5/5 상태"
sudo docker compose ps
echo
echo "완료. 브라우저에서 http://$(curl -s --max-time 5 https://checkip.amazonaws.com || echo '<서버 IP>') 로 접속한다."
echo "문제 에디터는 서버 로컬에만 열려 있다. 로컬에서 터널을 뚫는다:"
echo "  ssh -i secrets/kaupc-ec2 -L 8088:127.0.0.1:8088 ubuntu@<서버 IP>"
