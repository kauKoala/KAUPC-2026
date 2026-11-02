# DOMjudge 로컬 채점 서버

> KAUPC 2026 운영에 쓴 저장소를 다음 대회 준비를 위해 보존한 사본이다. 이 저장소에서는 자동 배포와 CI가 돌지 않는다.
> 워크플로는 `.github/workflows-archive/`에 있다. 다시 쓰려면 `.github/workflows/`로 옮기고 저장소 비밀값과 AWS 값을 채운다.
> 계정 비밀번호와 서버 식별값은 지웠다. `bootstrap/accounts.yaml`의 `CHANGE_ME`, `deploy/aws/Caddyfile`의 이메일을 대회 전에 바꾼다.

`docker compose` 기반. mariadb + domserver + judgehost 3개 컨테이너.

## 실행 / 종료

**가장 쉬운 방법**: [`DOMjudge 실행.bat`](DOMjudge%20실행.bat) 더블클릭 — Docker Desktop 확인/기동, 컨테이너 기동, 외부 주소 출력까지 전부 자동입니다.

```powershell
cd <저장소 폴더>
.\start.ps1       # 최초 기동: DB/domserver 초기화 → 비밀번호 추출 → judgehost 기동까지 자동
.\start-all.ps1   # 이후 재기동: Docker Desktop 확인 + 컨테이너 기동 + 외부 주소 출력 (실행.bat이 이걸 호출함)
.\stop.ps1        # 전체 종료 (데이터는 볼륨에 유지됨)
```

## 접속 정보

- 로컬: http://localhost:12345/
- 같은 네트워크(랜): http://<내부IP>:12345/  예) `ipconfig`로 확인

계정:
- admin / (start.ps1 실행 시 콘솔에 출력됨, 컨테이너 안 `/opt/domjudge/domserver/etc/initial_admin_password.secret`)
- judge 비밀번호는 `.env`의 `JUDGEDAEMON_PASSWORD`에 저장됨 (judgehost 컨테이너 인증용, 대회 참가자와 무관)

## 클라우드 이전 시 (cloud-native 대비)

`docker-compose.yml` 하나로 완결되어 있어 AWS EC2 등 아무 Docker Desktop/Engine 환경에 폴더째 복사 후
`docker compose up -d` 로 그대로 재현됩니다. 단, judgehost는 `privileged: true` + `cgroup: host` 필요 —
컨테이너 서비스(ECS Fargate 등)가 아니라 **VM 위 Docker**(EC2, Lightsail 등)를 써야 합니다.

## 문제 해결

- `docker compose logs domserver` / `judgehost` — 로그 확인
- judgehost가 "No submissions in queue" 반복 출력 = 정상 (대기 중)
- 컴파일러/채점 언어는 domserver 웹 UI → Admin → Languages 에서 활성화 (기본 다수 언어 이미 켜져 있음)
- **Docker Desktop이 "unexpected error"로 계속 죽는 경우**: 이 PC에서는 `EnableDockerAI`(Docker Desktop의 AI 기능) 설정이 원인이었습니다.
  `%APPDATA%\Docker\settings-store.json` 에서 `EnableDockerAI: false` 로 꺼두면 재발하지 않습니다.
  (같은 오류 메시지에 `dockerInference` 파이프 관련 내용이 있으면 이 문제일 가능성이 높습니다.)
- Tailscale Funnel이 502를 내면 대부분 Docker Desktop/domserver가 죽어있는 것 — `docker ps` 로 컨테이너 상태부터 확인
