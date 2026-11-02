#!/bin/sh
set -eu

console=/opt/domjudge/domserver/webapp/bin/console

exists() {
  "$console" api:call "$1" >/dev/null 2>&1
}

import_once() {
  endpoint=$1
  shift
  "$console" api:call "$@" "$endpoint"
}

db_query() {
  mariadb -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -N -B -e "$1"
}

db_exec() {
  mariadb -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "$1"
}

problem_id_from() {
  sed -n 's/^externalid *= *//p' "$1/domjudge-problem.ini" | head -n 1 | tr -d '\r'
}

problem_entry_from() {
  awk -v pid="$2" '
    /^- / { keep = ($0 ~ "^- id: *" pid "[[:space:]]*$") }
    keep { print }
  ' "$1"
}

build_archive() {
  source_dir=$1
  archive=$2
  (
    cd "$source_dir"
    contents="problem.yaml domjudge-problem.ini problem_statement submissions data"
    if [ -d output_validators ]; then
      contents="$contents output_validators"
    fi
    # 경로는 이 스크립트가 고정한 패키지 루트의 이름뿐이다.
    # shellcheck disable=SC2086
    zip -q -r "$archive" $contents
  )
}

# 저장소가 단일 원본이므로, 파일 쪽 테스트 집합이 DB와 다르면 DB 쪽을 비운 뒤 다시 넣는다.
# 지우지 않고 재import하면 DOMjudge가 rankindex 중복으로 실패한다.
# 채점 이력을 남기려고 행을 삭제하는 대신 DOMjudge와 같은 방식으로 deleted 플래그를 세운다.
testcases_on_disk() {
  ( cd "$1/data" 2>/dev/null && ls ./*/*.in 2>/dev/null | sed 's|.*/||; s|\.in$||' | sort | tr '\n' ' ' )
}

testcases_in_db() {
  db_query "SELECT orig_input_filename FROM testcase WHERE probid = $1 AND deleted = 0 ORDER BY orig_input_filename;" | tr '\n' ' '
}

reset_testcases_if_changed() {
  source_dir=$1
  problem_id=$2
  probid=$(db_query "SELECT probid FROM problem WHERE externalid = '$problem_id' LIMIT 1;")
  [ -n "$probid" ] || return 0
  disk=$(testcases_on_disk "$source_dir")
  stored=$(testcases_in_db "$probid")
  [ -n "$stored" ] || return 0
  if [ "$disk" != "$stored" ]; then
    echo "testcase set changed for $problem_id, clearing DB copy before import"
    db_exec "UPDATE testcase SET deleted = 1, probid = NULL WHERE probid = $probid AND deleted = 0;"
  fi
}

# bin/console api:call은 DELETE를 지원하지 않아 HTTP로 직접 부른다.
api_delete() {
  password=$(cat /opt/domjudge/domserver/etc/initial_admin_password.secret)
  curl -fsS -o /dev/null -u "admin:$password" -X DELETE "http://domserver/api/v4/$1"
}

# 계정은 DB에 없는 것만 등록한다. 이미 있는 계정을 다시 등록하면 비밀번호 해시가 새로 바뀌고,
# DOMjudge는 해시가 바뀐 계정의 로그인 세션을 모두 끊는다. provisioner는 문제를 저장할 때마다 돌기 때문에
# 다시 등록하면 운영자와 참가자가 저장할 때마다 로그아웃된다.
# 기존 계정의 비밀번호나 이름을 바꾸려면 관리자 화면에서 바꾼다.
import_new_accounts() {
  existing=" $(db_query 'SELECT username FROM `user`;' | tr '\n' ' ') "
  missing=$(mktemp)
  awk -v existing="$existing" '
    function flush() {
      if (block != "" && index(existing, " " name " ") == 0) printf "%s", block
      block = ""
      name = ""
    }
    /^- / { flush() }
    { block = block $0 "\n" }
    /^(- )? *username:/ {
      name = $0
      sub(/^(- )? *username: */, "", name)
      gsub(/["\047\r ]/, "", name)
    }
    END { flush() }
  ' "$1" > "$missing"
  if [ -s "$missing" ]; then
    import_once users/accounts -m POST -f yaml="$missing" || true
  fi
  rm -f "$missing"
}

# 팀도 DB에 없는 것만 등록한다. 이미 있는 팀을 다시 가져오면 teams.json에 없는 display_name이
# 비워져서, 참가자가 처음 로그인할 때 정한 이름이 배포할 때마다 지워진다.
import_new_teams() {
  existing=$(db_query 'SELECT externalid FROM team;' | tr '\n' ' ')
  missing=$(mktemp)
  php -r '
    $teams = json_decode(file_get_contents($argv[1]), true);
    $existing = array_flip(preg_split("/\s+/", trim($argv[2])));
    $new = array_values(array_filter($teams, fn($team) => !isset($existing[$team["id"]])));
    if ($new) file_put_contents($argv[3], json_encode($new, JSON_UNESCAPED_UNICODE));
  ' "$1" "$existing" "$missing"
  if [ -s "$missing" ]; then
    import_once users/teams -m POST -f json="$missing" || true
  fi
  rm -f "$missing"
}

# 순위표에는 이름을 정한 참가자만 보인다. 팀은 처음 한 번만 가져오므로 이미 있는 팀의 분류는 여기서 맞춘다.
# 운영진 테스트 계정은 staff, 이름이 빈 참가자는 pending, 이름을 정한 참가자는 participants. 앞의 둘은 숨긴 분류다.
STAFF_TEAMS="'a','b','c','d','tester'"
sync_team_visibility() {
  db_exec "UPDATE team t JOIN team_category staff ON staff.externalid = 'staff' SET t.categoryid = staff.categoryid WHERE t.externalid IN ($STAFF_TEAMS);"
  db_exec "UPDATE team t
    JOIN team_category current ON current.categoryid = t.categoryid
    JOIN team_category pending ON pending.externalid = 'pending'
    JOIN team_category shown ON shown.externalid = 'participants'
    SET t.categoryid = IF(COALESCE(TRIM(t.display_name), '') = '', pending.categoryid, shown.categoryid)
    WHERE current.externalid IN ('participants', 'pending') AND t.externalid NOT IN ($STAFF_TEAMS);"
}

# provisioner는 문제를 저장할 때마다 돈다. 지난번에 넣은 문제 파일의 해시를 여기 남긴다.
STATE_DIR=${STATE_DIR:-/state}
mkdir -p "$STATE_DIR"

package_digest() {
  (
    cd "$1"
    find problem.yaml domjudge-problem.ini problem_statement submissions data output_validators -type f 2>/dev/null \
      | LC_ALL=C sort | xargs -d '\n' sha256sum | sha256sum | cut -d ' ' -f 1
  )
}

problem_has_testcases() {
  count=$(db_query "SELECT COUNT(*) FROM testcase t JOIN problem p ON p.probid = t.probid WHERE p.externalid = '$1' AND t.deleted = 0;")
  [ "${count:-0}" -gt 0 ]
}

# 라벨을 바꿀 때 두 문제가 잠시 같은 라벨을 갖지 않도록 먼저 임시 라벨로 비켜 둔다.
park_labels() {
  db_exec "UPDATE contestproblem cp JOIN contest c ON c.cid = cp.cid SET cp.shortname = CONCAT('~', cp.probid) WHERE c.externalid = '$1';"
}

set_label() {
  db_exec "UPDATE contestproblem cp JOIN contest c ON c.cid = cp.cid JOIN problem p ON p.probid = cp.probid SET cp.shortname = '$3', cp.color = '$4' WHERE c.externalid = '$1' AND p.externalid = '$2';"
}

# 저장소에서 빠진 문제는 대회와의 연결만 끊는다. 문제 자체와 제출 기록은 DB에 남는다.
unlink_removed_problems() {
  contest_dir=$1
  contest_id=$2
  cid=$(db_query "SELECT cid FROM contest WHERE externalid = '$contest_id' LIMIT 1;")
  [ -n "$cid" ] || return 0
  wanted=" "
  for package_dir in "$contest_dir"/*/; do
    package_dir=${package_dir%/}
    source_dir="$package_dir"
    if [ -f "$package_dir/source.txt" ]; then
      source_dir=$(cd "$contest_dir/$(tr -d '\r' < "$package_dir/source.txt")" && pwd)
    fi
    [ -f "$source_dir/problem.yaml" ] || continue
    wanted="$wanted$(problem_id_from "$source_dir") "
  done
  for linked in $(db_query "SELECT p.externalid FROM contestproblem cp JOIN problem p ON p.probid = cp.probid WHERE cp.cid = $cid;"); do
    case "$wanted" in
      *" $linked "*) ;;
      *)
        echo "unlinking $linked from $contest_id (not in repository)"
        api_delete "contests/$contest_id/problems/$linked" || echo "failed to unlink $linked from $contest_id"
        ;;
    esac
  done
}

import_once users/groups -m POST -f json=/bootstrap/groups.json || true
import_new_teams /bootstrap/teams.json
import_new_accounts /bootstrap/accounts.yaml

if exists contests/demo; then
  db_exec "UPDATE contest SET enabled = 0 WHERE shortname = 'demo'"
fi

# 저장소에서 지운 대회는 DB에서 끈다. 제출 기록은 남기고 참가자 화면에서만 사라진다.
for retired in fivemin; do
  db_exec "UPDATE contest SET enabled = 0 WHERE externalid = '$retired';"
done

# 운영진 QA용 대회는 참가자와 공개 순위표에서 숨긴다. 끄면(enabled = 0) API가 대회를 못 찾아
# 다음 배포 때 다시 만들려다 실패하고, KAUPC가 빌려 쓰는 TEST 문제도 갱신되지 않는다.
# 그래서 켜 둔 채로 어느 팀도 참가하지 않게 한다. 운영자 화면에서는 그대로 보인다.
for staff_only in test kaupc-open; do
  db_exec "UPDATE contest SET public = 0, open_to_all_teams = 0 WHERE externalid = '$staff_only';"
  db_exec "DELETE ct FROM contestteam ct JOIN contest c ON c.cid = ct.cid WHERE c.externalid = '$staff_only';"
  db_exec "DELETE cc FROM contestteamcategory cc JOIN contest c ON c.cid = cc.cid WHERE c.externalid = '$staff_only';"
done

db_exec "UPDATE team SET enabled = 0 WHERE externalid = 'exteam'"

# 한 번만 돌릴 DB 수정. 상태 파일을 남겨 다음 배포에서 다시 돌지 않게 한다.
run_once() {
  marker="$STATE_DIR/once-$1"
  [ -e "$marker" ] && return 0
  db_exec "$2" && touch "$marker"
}

# 2026-10-28 운영 서버에서 예비 계정 user_027로 이름 정하기를 시험했다. 나눠 주기 전에 되돌린다.
run_once reset-user027-nickname "UPDATE team SET display_name = NULL WHERE externalid = 'user_027';"
sync_team_visibility

# 참가자가 제출 상세에서 자기 코드를 볼 수 있게 한다. 참가자 화면이 이 내려받기 주소로 코드를 불러온다.
db_exec "INSERT INTO configuration (name, value) VALUES ('allow_team_submission_download', 'true') ON DUPLICATE KEY UPDATE value = 'true';"

# 대회끼리 문제를 빌려 쓴다(KAUPC C → TEST J, TEST A → KAUPC I). 빈 DB에서는 빌려 올 문제가 아직 없으므로
# 먼저 모든 대회의 자기 문제를 넣고(own), 그다음 빌려 쓰는 문제를 붙인다(reused).
for pass in own reused; do
for contest_dir in /contest-data/*; do
  [ -d "$contest_dir" ] || continue
  contest_id=$(sed -n 's/^id: *//p' "$contest_dir/contest.yaml" | head -n 1 | tr -d '\r')
  if [ "$pass" = own ]; then
    if ! exists "contests/$contest_id"; then
      import_once contests -m POST -f "yaml=$contest_dir/contest.yaml"
    fi
    # 대회 이름은 contest.yaml을 따른다. 처음 만든 뒤에 바꿔도 반영되게 한다.
    contest_name=$(sed -n 's/^name: *//p' "$contest_dir/contest.yaml" | head -n 1 | tr -d '\r')
    if [ -n "$contest_name" ]; then
      db_exec "UPDATE contest SET name = '$contest_name' WHERE externalid = '$contest_id';"
    fi
    unlink_removed_problems "$contest_dir" "$contest_id"
    park_labels "$contest_id"
  fi
  find "$contest_dir" -mindepth 1 -maxdepth 1 -type d | sort | while read -r package_dir; do
    label=$(basename "$package_dir")
    source_dir="$package_dir"
    if [ -f "$package_dir/source.txt" ]; then
      [ "$pass" = reused ] || continue
      source_dir=$(cd "$contest_dir/$(tr -d '\r' < "$package_dir/source.txt")" && pwd)
    else
      [ "$pass" = own ] || continue
    fi
    [ -f "$source_dir/problem.yaml" ] || continue

    problem_id=$(problem_id_from "$source_dir")
    # 이 대회의 problems.yaml에 적힌 색을 쓴다. 없으면 원본 대회의 색을 쓴다.
    entry=$(problem_entry_from "$contest_dir/problems.yaml" "$problem_id")
    [ -n "$entry" ] || entry=$(problem_entry_from "$(dirname "$source_dir")/problems.yaml" "$problem_id")
    color=$(printf '%s\n' "$entry" | sed -n 's/^  color: *//p' | head -n 1 | tr -d "'\r")
    rgb=$(printf '%s\n' "$entry" | sed -n 's/^  rgb: *//p' | head -n 1 | tr -d "'\r")
    [ -n "$color" ] || color=SteelBlue
    [ -n "$rgb" ] || rgb='#4682B4'

    if [ "$source_dir" = "$package_dir" ]; then
      if ! exists "contests/$contest_id/problems/$problem_id"; then
        entry_file=$(mktemp --suffix=.yaml)
        printf '%s\n' "$entry" > "$entry_file"
        import_once "contests/$contest_id/problems/add-data" -m POST -f "data=$entry_file"
        rm -f "$entry_file"
      fi
      # 문제 파일이 지난번에 넣은 것과 같으면 다시 압축·등록하지 않는다.
      # 저장할 때마다 모든 문제를 다시 넣으면 서버가 몇 분씩 바빠진다.
      state="$STATE_DIR/$contest_id-$problem_id.sha256"
      digest=$(package_digest "$source_dir")
      if [ -f "$state" ] && [ "$(cat "$state")" = "$digest" ] && problem_has_testcases "$problem_id"; then
        echo "unchanged $contest_id/$problem_id, skipping import"
      else
        reset_testcases_if_changed "$source_dir" "$problem_id"
        archive=$(mktemp --suffix=.zip)
        rm -f "$archive"
        build_archive "$source_dir" "$archive"
        import_once "contests/$contest_id/problems" -m POST -d "problem=$problem_id" -f "zip=$archive"
        rm -f "$archive"
        printf '%s\n' "$digest" > "$state"
      fi
    elif ! exists "contests/$contest_id/problems/$problem_id"; then
      import_once "contests/$contest_id/problems/$problem_id" -m PUT -d "label=$label" -d "color=$color" -d "rgb=$rgb"
    fi
    # 이미 대회에 붙어 있던 문제도 저장소의 라벨과 색을 따른다.
    set_label "$contest_id" "$problem_id" "$label" "$rgb"
  done
done
done

# 끝난 대회의 순위표를 그대로 남긴다. 대회가 모든 팀에게 열려 있으면 나중에 생긴 팀(게스트, 뒤늦게 이름을 정한 계정)이
# 끝난 대회 순위표에 0문제 줄로 끼어든다. 처음 한 번, 그때 순위표에 보이던 팀과 제출한 팀만 대회에 묶고 문을 닫는다.
# 대회 기록(제출, 채점, 점수)은 건드리지 않는다.
# 비공개로 돌려 로그인하지 않은 방문자와 게스트에게는 보이지 않게 한다. 대회에 묶인 KAUPC 계정과 운영자 화면에는 남는다.
# 비활성 시각을 쓰거나 끄면(enabled = 0) 관리자 API도 대회를 못 찾아 다음 배포가 대회를 다시 만들려다 실패한다.
FINISHED_CONTESTS="kaupc"
lock_finished_contest() {
  cid=$(db_query "SELECT cid FROM contest WHERE externalid = '$1' LIMIT 1;")
  [ -n "$cid" ] || return 0
  run_once "lock-$1-teams" "INSERT IGNORE INTO contestteam (cid, teamid)
      SELECT $cid, t.teamid FROM team t JOIN team_category tc ON tc.categoryid = t.categoryid
      WHERE tc.externalid IN ('participants', 'staff')
         OR t.teamid IN (SELECT s.teamid FROM submission s WHERE s.cid = $cid);
    DELETE FROM contestteamcategory WHERE cid = $cid;"
  db_exec "UPDATE contest SET public = 0, open_to_all_teams = 0 WHERE cid = $cid;"
}
for finished in $FINISHED_CONTESTS; do
  lock_finished_contest "$finished"
done

# 공개 대회는 로그인 없이 문제와 순위표를 보고, 게스트 계정으로 바로 제출한다. 게스트 분류만 참가해 순위표에 게스트만 보인다.
OPEN_CONTESTS="kaupcopen"
for open_contest in $OPEN_CONTESTS; do
  db_exec "UPDATE contest SET enabled = 1, public = 1, open_to_all_teams = 0 WHERE externalid = '$open_contest';"
  db_exec "DELETE ct FROM contestteam ct JOIN contest c ON c.cid = ct.cid WHERE c.externalid = '$open_contest';"
  db_exec "INSERT IGNORE INTO contestteamcategory (cid, categoryid)
      SELECT c.cid, tc.categoryid FROM contest c JOIN team_category tc ON tc.externalid = 'guests' WHERE c.externalid = '$open_contest';"
  # 프리즈 0시간을 넣어도 DOMjudge는 duration이 크면 대회 중간 시각을 프리즈로 계산한다. 프리즈를 아예 지운다.
  db_exec "UPDATE contest SET freezetime = NULL, freezetime_string = NULL WHERE externalid = '$open_contest';"
done
