# KAUPC 결과 보존과 공개 대회

KAUPC2026(`kaupc`)은 끝났다. 결과는 그대로 남기고, 같은 문제로 상시 공개 대회 **KAUPC2026 Open**(`kaupcopen`)을 연다.
공개 대회는 아이디·비밀번호 없이 게스트로 참여해 제출한다.

## 무엇이 바뀌나

| 대상 | 내용 |
| --- | --- |
| `problems/contests/OPEN/` | 공개 대회. 각 라벨 폴더에는 `source.txt`(`../KAUPC/<라벨>`)만 있다. 문제 파일을 복제하지 않고 KAUPC 문제를 그대로 연결한다. 기간은 2주(`336:00:00`), 프리즈 없음 |
| `bootstrap/provision.sh` | 끝난 `kaupc`는 처음 한 번, 그때 순위표에 보이던 팀(`participants`, `staff`)과 대회 중 제출한 팀만 묶고 `open_to_all_teams = 0`으로 닫는다. 이후 생기는 게스트나 뒤늦게 이름을 정한 계정이 KAUPC 순위표에 끼지 않는다. 그리고 `public = 0`으로 비공개로 돌린다. 비활성 시각을 쓰면 관리자 API가 대회를 못 찾아 다음 배포가 실패하므로 쓰지 않는다. 제출·채점·점수는 건드리지 않는다. `kaupcopen`은 공개(`public = 1`)이고 `guests` 분류만 참가한다. 순위표에는 게스트만 보인다 |
| `bootstrap/groups.json` | `guests`(순위표에 보임) 분류 추가. `guest-pending`은 예전 방식의 흔적으로 쓰지 않는다 |
| `custom/nginx/domjudge-site.conf` | **로그인 화면이 없다.** 로그인 화면을 여는 요청(`GET /login`)을 DOMjudge 대신 에디터의 `/participant/enter`로 보낸다. 로그인 안 한 방문자는 어느 주소로 오든 DOMjudge가 `/login`으로 보내므로, 결국 모두 여기로 온다 |
| 문제 에디터 `/participant/enter` | 처음 온 브라우저에 게스트 팀·계정을 만들고, 서버가 그 계정으로 DOMjudge에 대신 로그인해 세션 쿠키를 넘긴 뒤 바로 대회 화면으로 보낸다. 계정은 `kaupc_guest` 쿠키(HttpOnly, 30일)에 남아 세션이 끊겨도 같은 계정으로 다시 들어간다. 접속 주소마다 시간당 30개, 전체 시간당 300개로 제한 |
| 첫 화면 | `/`와 DOMjudge 공개 화면(`/public`)은 공개 대회가 보이는 대회 목록(`/contest`)으로 간다 |
| 대회 목록 | 게스트와 비로그인 방문자에게는 공개 대회만 보인다. KAUPC는 비공개지만 대회에 묶인 KAUPC 계정과 운영자 화면에는 남는다. 끄지 않으므로 결과와 관리자 API는 그대로다 |
| 채점 현황 탭 | 대회 탭(문제 목록·제출·**채점 현황**·순위표·질의응답)에 추가. 운영자 화면의 제출 목록처럼 공개 대회의 모든 제출(번호·시각·참가자·문제·언어·결과·실행 시간)을 보인다. 운영자 제출 목록처럼 목록에 테스트별 결과가 바로 보이고, 제출을 누르면 운영자 제출 상세와 같은 구성의 화면(`/contest/status/<번호>`)에서 코드, 컴파일 결과, 실행한 테스트의 입력·정답·프로그램 출력을 본다. 입출력과 컴파일 결과는 에디터가 DB에서 읽는다. KAUPC 제출은 열리지 않는다. 에디터 `/participant/submissions`가 관리자 API로 모아 5초씩 캐시한다 |
| 운영진·KAUPC 계정 | 게스트 화면 오른쪽 위 **로그인** 버튼(`/login?account=1`)으로 원래 로그인 화면을 쓴다. 로그인에 실패해도 그 화면에 남는다 |
| 운영자 화면 | `/jury`는 권한을 요구한다. 로그인 안 했거나 게스트면 계정 로그인 화면으로 간다 |

게스트에게는 이름을 묻지 않는다. "게스트 xxxxxx"라는 이름으로 채점 현황에 보인다. 게스트 화면에는 순위표 탭이 없다.
다른 사람의 코드는 채점 현황 탭에서 볼 수 있다. KAUPC 참가자 계정은 공개 대회에 참여하지 않는다.

게스트 기록은 그 브라우저의 쿠키에만 묶인다. 브라우저 데이터를 지우거나 다른 기기에서 들어오면 새 게스트가 된다.

## 배포 순서

master에 푸시하면 `deploy` 워크플로가 곧바로 스택 갱신과 provisioner까지 실행한다. 백업은 반드시 master에 합치기 전에 끝낸다.
아래 3번의 명령은 워크플로가 실패했을 때 서버에서 직접 실행하는 절차다.

운영 DB에만 있는 빈 대회 `kaupc-open`(제출 0건)은 TEST처럼 비공개로 두고 어느 팀도 묶지 않는다.

1. **먼저 DB를 백업한다.** 결과 보존의 마지막 안전장치다.

   ```bash
   docker compose exec -T mariadb sh -c 'mariadb-dump -u root -p"$MYSQL_ROOT_PASSWORD" domjudge' > kaupc2026-final.sql
   ```

2. KAUPC는 이제 비로그인 방문자에게 보이지 않는다. 결과를 따로 공개하려면 이 배포 전에 순위표를 저장해 둔다.
3. 코드를 받고 에디터·nginx·Caddy·provisioner를 갱신한다.

   ```bash
   git pull
   ```

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.cloud.yml up -d --build problem-editor
   ```

   ```bash
   docker compose exec domserver nginx -s reload
   ```

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.cloud.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
   ```

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.cloud.yml up -d provisioner
   ```

4. `python scripts/check-sync.py`로 `kaupcopen`에 A~K가 붙었는지 확인한다.
5. 시크릿 창에서 `https://kaupc2026.me/`에 들어가 로그인 화면·이름 묻기 없이 바로 문제 목록이 나오는지, 제출하면 제출 상세와 **채점 현황** 탭에 보이는지, 대회 목록에 공개 대회만 있는지 확인한다. 운영진은 `/login?account=1`로 로그인해 KAUPC가 운영자 화면에 그대로 있는지 본다.

## 알아 둘 것

- `contest.yaml`의 시작 시각·기간은 대회를 처음 만들 때만 쓰인다. 만든 뒤 바꾸려면 운영자 화면에서 바꾼다.
- 게스트 참여를 끄려면 `.env`에 `GUEST_SIGNUP=0`을 넣고 `problem-editor`를 다시 띄운다. 이미 만든 게스트 계정은 그대로 로그인된다. 끄면 새 방문자에게는 오류 화면이 보이니, 그때는 nginx의 `/login` 가로채기도 함께 지운다.
- 공개 대회와 KAUPC는 같은 문제 레코드를 쓴다. 테스트 데이터를 고치면 두 대회 모두에 적용되지만, 리저지를 하지 않는 한 KAUPC의 기존 판정은 바뀌지 않는다. KAUPC 제출은 리저지하지 않는다.
- KAUPC를 닫는 작업은 provisioner 상태 볼륨의 `once-lock-kaupc-teams` 표식으로 한 번만 돈다. 다시 묶어야 하면 그 파일을 지우고 provisioner를 돌린다.
