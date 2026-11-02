#!/usr/bin/env bash
# 운영 서버에서 5분짜리 리허설 대회를 돌려 채점 흐름 전체를 확인한다.
#
#   bash deploy/aws/dry_run.sh
#
# 하는 일:
#   1. 1분 뒤 시작하는 5분짜리 대회를 새로 만든다 (TEST의 apb, starprint를 붙인다)
#   2. 시작하자마자 a, b, c, tester 네 팀 이름으로 동시에 제출한다
#   3. 모든 제출이 기대한 판정을 받았는지 확인한다
#   4. 대회가 끝난 뒤 순위표의 푼 문제 수와 벌점을 확인한다
#   5. 참가자에게 보이지 않도록 대회를 끈다
#
# 관리자 비밀번호는 서버에 있는 initial_admin_password.secret을 읽어 쓴다. 저장소에는 남기지 않는다.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/oj-domjudge}"
BASE="${BASE:-http://localhost/api/v4}"
cd "$REPO_DIR"

compose() { sudo docker compose "$@"; }
password=$(compose exec -T domserver cat /opt/domjudge/domserver/etc/initial_admin_password.secret | tr -d '\r\n')
api() { curl -sS --fail-with-body -u "admin:$password" "$@"; }

stamp=$(date +%m%d%H%M)
cid="dryrun$stamp"
start=$(date -d '+60 seconds' '+%Y-%m-%dT%H:%M:%S%:z')
work=$(mktemp -d)
disable_contest() {
  compose exec -T mariadb sh -c "mariadb -u root -p\"\$MYSQL_ROOT_PASSWORD\" domjudge -e \"UPDATE contest SET enabled = 0, public = 0 WHERE externalid = '$cid'\"" || true
}
# 중간에 실패해도 리허설 대회가 참가자 화면에 남지 않게 한다.
trap 'status=$?; disable_contest; echo "대회 $cid 비활성화"; rm -rf "$work"; exit $status' EXIT

echo "== 대회 $cid 생성 (시작 $start, 5분)"
cat > "$work/contest.yaml" <<EOF
id: $cid
name: DRY RUN $stamp
formal_name: DRY RUN $stamp
start_time: $start
duration: 0:05:00
penalty_time: 20
EOF
api -o /dev/null -X POST -F "yaml=@$work/contest.yaml" "$BASE/contests"

cat > "$work/problems.yaml" <<EOF
- id: apb
  label: A
  color: SteelBlue
  rgb: '#4682B4'
- id: starprint
  label: B
  color: SeaGreen
  rgb: '#2E8B57'
EOF
api -o /dev/null -X POST -F "data=@$work/problems.yaml" "$BASE/contests/$cid/problems/add-data"
api "$BASE/contests/$cid/problems" | python3 -c 'import sys,json; print("   문제:", ", ".join(p["label"]+"="+p["id"] for p in json.load(sys.stdin)))'

apb_ac=problems/contests/TEST/B/submissions/accepted/solution.py
star_ac=problems/contests/TEST/E/submissions/accepted/solution.py
star_wa=problems/contests/TEST/E/submissions/wrong_answer/zero_based.py

# 팀 문제 파일 기대판정. 같은 팀의 제출도 서로 동시에 보낸다.
plan="a apb $apb_ac AC
a starprint $star_ac AC
b starprint $star_wa WA
b starprint $star_ac AC
c apb $apb_ac AC
c starprint $star_wa WA
tester starprint $star_ac AC
tester starprint $star_wa WA
tester apb $apb_ac AC"

echo "== 시작 대기"
while [ "$(date +%s)" -lt "$(date -d "$start" +%s)" ]; do sleep 1; done
sleep 2

echo "== 네 팀 동시 제출 ($(echo "$plan" | wc -l)건)"
: > "$work/submitted"
i=0
while read -r team problem file expected; do
  i=$((i + 1))
  (
    id=$(api -X POST -F "problem=$problem" -F language=python3 -F "team_id=$team" \
      -F "code[]=@$file" "$BASE/contests/$cid/submissions" \
      | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
    echo "$id $team $problem $expected" >> "$work/submitted"
  ) &
done <<< "$plan"
wait
sort -n "$work/submitted" | sed 's/^/   제출 /'
[ "$(wc -l < "$work/submitted")" -eq "$i" ] || { echo "제출 일부가 실패했다"; exit 1; }

echo "== 채점 대기"
deadline=$(( $(date +%s) + 240 ))
while :; do
  api "$BASE/contests/$cid/judgements" > "$work/judgements.json"
  done_count=$(python3 - "$work/judgements.json" <<'PY'
import sys, json
print(sum(1 for j in json.load(open(sys.argv[1])) if j.get("judgement_type_id") and j.get("end_time")))
PY
)
  echo "   $done_count / $i 완료"
  [ "$done_count" -ge "$i" ] && break
  [ "$(date +%s)" -lt "$deadline" ] || { echo "채점이 4분 안에 끝나지 않았다"; exit 1; }
  sleep 5
done

python3 - "$work/submitted" "$work/judgements.json" <<'PY'
import sys, json
judged = {}
for j in json.load(open(sys.argv[2])):
    if j.get("judgement_type_id"):
        judged[j["submission_id"]] = j
bad = 0
for line in open(sys.argv[1]):
    sid, team, problem, expected = line.split()
    j = judged[sid]
    got = j["judgement_type_id"]
    runtime = j.get("max_run_time")
    mark = "OK " if got == expected else "BAD"
    bad += got != expected
    print(f"   {mark} 제출 {sid:>4} {team:<7} {problem:<10} 기대 {expected} 실제 {got} ({runtime}s)")
sys.exit(1 if bad else 0)
PY

end=$(( $(date -d "$start" +%s) + 300 ))
echo "== 대회 종료 대기 ($(( end - $(date +%s) ))초)"
while [ "$(date +%s)" -lt "$end" ]; do sleep 5; done
sleep 5

echo "== 최종 순위표"
api "$BASE/contests/$cid/scoreboard" > "$work/scoreboard.json"
python3 - "$work/scoreboard.json" <<'PY'
import sys, json
board = json.load(open(sys.argv[1]))
# 같은 팀의 오답과 정답을 동시에 보내므로 어느 쪽이 먼저 접수될지 모른다. 벌점은 보여 주기만 한다.
expected = {"a": 2, "tester": 2, "b": 1, "c": 1}
bad = 0
for row in board["rows"]:
    team = row["team_id"]
    solved = row["score"]["num_solved"]
    penalty = row["score"]["total_time"]
    if team not in expected:
        continue
    want_solved = expected[team]
    ok = solved == want_solved
    bad += not ok
    print(f"   {'OK ' if ok else 'BAD'} {row['rank']:>2}위 {team:<7} {solved}문제 벌점 {penalty}분 (기대 {want_solved}문제)")
missing = set(expected) - {r["team_id"] for r in board["rows"]}
if missing:
    print("   순위표에 없는 팀:", ", ".join(sorted(missing)))
    bad += 1
sys.exit(1 if bad else 0)
PY

echo "== 모든 확인 통과: $cid"
