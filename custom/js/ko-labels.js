// 참가자 화면(공개/팀 인터페이스) 한글 라벨 오버레이.
// DOMjudge 코어를 건드리지 않고 텍스트만 치환 — 이미지 업데이트해도 안 깨짐.
// 실제 /public, /public/problems, 로그인 페이지의 렌더링 결과를 확인해서 채운 사전임.
(function () {
  var DICT = {
    // 로그인
    "Please sign in": "로그인",
    "Username": "아이디",
    "Password": "비밀번호",
    "Sign in": "로그인",
    "Login": "로그인",
    "Logout": "로그아웃",
    "Log out": "로그아웃",
    "Invalid credentials.": "아이디 또는 비밀번호가 올바르지 않습니다.",

    // 상단 네비게이션
    "Home": "홈",
    "Problems": "문제",
    "Problemset": "문제 목록",
    "Submit": "제출",
    "Submissions": "제출 현황",
    "Clarifications": "질의응답",
    "Scoreboard": "순위표",
    "Contest": "대회",
    "Documentation": "도움말",
    "Change contest": "대회 변경",
    "contest over": "대회 종료",

    // 문제 목록 페이지
    "statement": "지문",
    "samples": "예제",
    "pass-fail": "정오",
    "interactive": "상호작용",
    "scoring": "점수제",
    "multipass": "멀티패스",
    "submit-answer": "답 제출",

    // 순위표
    "Filter": "필터",
    "Categories": "분류",
    "Self-Registered": "자가 등록",
    "Participants": "참가자",
    "Observers": "옵저버",
    "rank": "순위",
    "team": "이름",
    "score": "점수",
    "Summary": "요약",
    "n/a": "-",
    "Cell colours": "셀 색상 안내",
    "Solved": "해결",
    "Solved first": "퍼스트 솔브",
    "Jury": "운영진",
    "Tried, incorrect": "시도함 (오답)",
    "Tried, pending": "시도함 (채점 중)",
    "Untried": "시도 안 함",
    "Loading...": "불러오는 중...",
    "No submissions": "제출 없음",
    "time": "시간",
    "language": "언어",
    "result": "결과",
    "on problem": "/ 문제:",
    "from": "보낸 사람",
    "to": "받는 사람",
    "subject": "제목",
    "text": "내용",
    "state": "상태",
    "who": "담당자",

    // 제출 폼
    "Problem": "문제",
    "Language": "언어",
    "Source file(s)": "소스 파일",
    "Source file": "소스 파일",
    "Source files": "소스 파일",
    "Files": "파일",
    "Select a language": "언어를 선택하세요",
    "Select a problem": "문제를 선택하세요",
    "Entry point": "엔트리 포인트",
    "The entry point for your code.": "코드 실행을 시작할 파일 또는 클래스입니다.",
    "Add another file": "파일 추가",
    "Submit code": "코드 제출",

    // 채점 결과 (verdict)
    "Correct": "정답",
    "Wrong answer": "오답",
    "Wrong Answer": "오답",
    "Time limit exceeded": "시간 초과",
    "Time Limit Exceeded": "시간 초과",
    "Run error": "런타임 에러",
    "Runtime Error": "런타임 에러",
    "Compiler error": "컴파일 에러",
    "Compile error": "컴파일 에러",
    "Memory limit exceeded": "메모리 초과",
    "Output limit exceeded": "출력 초과",
    "No output": "출력 없음",
    "Too late": "대회 종료 후 제출",
    "too-late": "대회 종료 후 제출",
    "problem": "문제",
    "lang": "언어",
    "Pending": "채점 대기 중",
    "Judging": "채점 중",
    "Queued": "대기 중",

    // 질의응답
    "Clarification request": "질문하기",
    "Clarification Requests": "내 질문",
    "Request clarification": "질문하기",
    "Send Clarification Request": "질문 보내기",
    "No clarification request.": "보낸 질문이 없습니다.",
    "No clarifications.": "공지나 답변이 없습니다.",
    "Recipient": "받는 사람",
    "Subject": "제목",
    "Message": "내용",
    "Send": "보내기",
    "General issue": "일반 질문",
    "Technical issue": "기술 문제",
    "Start typing to see a preview of your message": "내용을 입력하면 미리보기가 표시됩니다",
    "rendered preview": "미리보기",
    "You have no unread clarifications.": "읽지 않은 공지나 답변이 없습니다.",
    "Sorry, an error has occurred: Not Found.": "오류가 발생했습니다: 페이지를 찾을 수 없습니다.",
    "Please contact a staff member for assistance.": "도움이 필요하면 운영진에게 문의하세요.",

    // Jury(운영자) 인터페이스
    "DOMjudge Jury interface": "DOMjudge 운영자 화면",
    "Before contest:": "대회 시작 전:",
    "During contest:": "대회 진행 중:",
    "Administrator:": "관리자:",
    "judgehosts": "채점 서버",
    "Judgehosts": "채점 서버",
    "clarifications": "질의응답",
    "submissions": "제출 현황",
    "Documentation:": "도움말:",
    "Contests": "대회 목록",
    "Executables": "실행 파일",
    "Languages": "언어 설정",
    "Team problemset page preview": "참가자 문제 목록 미리보기",
    "Users": "사용자",
    "Teams": "참가자",
    "Team Categories": "참가자 분류",
    "Team Affiliations": "참가자 소속",
    "Judging verifier": "채점 검증기",
    "Compiler and runner versions": "컴파일러/실행기 버전",
    "Balloon Status": "풍선 배달 현황",
    "Internal Errors": "내부 오류",
    "Rejudgings": "재채점",
    "Statistics/Analysis": "통계/분석",
    "Queue tasks": "대기열 작업",
    "Configuration settings": "환경설정",
    "Config checker": "설정 점검",
    "Import / export": "가져오기/내보내기",
    "Manage team passwords": "참가자 비밀번호 관리",
    "Refresh scoreboard cache": "순위표 캐시 새로고침",
    "Audit log": "감사 로그",
    "DOMjudge manual": "DOMjudge 매뉴얼",
    "Team manual": "참가자 매뉴얼",
    "API documentation": "API 문서",
    "See also the": "참고:",

    // 제출 상세 (페이지와 모달 모두)
    "Submission details": "제출 정보",
    "Problem:": "문제:",
    "Submitted:": "제출 시각:",
    "Language:": "언어:",
    "Result:": "결과:",
    "Compilation:": "컴파일:",
    "Compilation": "컴파일",
    "successful": "성공",
    "failed": "실패",
    "with the following output": "· 컴파일러 출력",
    "There were no compiler errors or warnings.": "컴파일 에러나 경고가 없습니다.",
    "Max. Runtime:": "최대 실행 시간:",
    "Download submission ZIP": "제출 파일 내려받기",
    "Run(s) on the provided sample data": "예제 실행 결과",
    "No sample cases available.": "예제가 없습니다.",
    "Run not finished yet.": "아직 실행 중입니다.",
    "Description": "설명",
    "Runtime": "실행 시간",
    "Program output": "프로그램 출력",
    "There was no program output.": "프로그램 출력이 없습니다.",
    "Judge message": "채점 메시지",
    "Error output (info/debug/errors)": "표준 에러 출력",
    "There was no stderr output.": "표준 에러 출력이 없습니다.",
    "Submission not found for this team or not judged yet.": "제출을 찾을 수 없거나 아직 채점되지 않았습니다.",
    "This submission is being ignored. It is not used in determining your score.": "이 제출은 무시되어 점수 계산에 쓰이지 않습니다.",

    // 공통 버튼
    "Save": "저장",
    "Cancel": "취소",
    "Close": "닫기",
    "Refresh": "새로고침",
    "Back": "뒤로",

    // ---- jury 관리자 화면 대량 일괄 추가 (20여 페이지 스캔) ----
    "# contests": "# 대회", "# problems": "# 문제", "# teams": "# 참가자", "# test cases": "# 테스트 케이스",
    "-- default compare script --": "-- 기본 비교 스크립트 --", "-- default run script --": "-- 기본 실행 스크립트 --",
    "-- no affiliation --": "-- 소속 없음 --", "-- no team --": "-- 참가자 없음 --",
    "Accepted": "정답", "Access token": "액세스 토큰", "Activate time:": "활성화 시각:",
    "Add existing user": "기존 사용자 추가", "Add new affiliation": "새 소속 추가", "Add new category": "새 분류 추가",
    "Add new contest": "새 대회 추가", "Add new executable": "새 실행 파일 추가", "Add new language": "새 언어 추가",
    "Add new problem": "새 문제 추가", "Add new rejudging": "새 재채점 추가", "Add new team": "새 참가자 추가",
    "Add new user": "새 사용자 추가", "Add problem": "문제 추가", "Add team": "참가자 추가", "Add user": "사용자 추가",
    "Add user to this team": "이 참가자에 사용자 추가", "Administrative User": "관리자", "Administrator": "관리자",
    "Affiliation": "소속", "Affiliations": "소속 목록", "All": "전체", "All available contests": "이용 가능한 모든 대회",
    "All teams": "모든 참가자", "Always": "항상", "Analyst mode": "분석 모드", "Apply filters": "필터 적용",
    "Auditlog": "감사 로그", "Auth methods:": "인증 방식:", "Authentication": "인증",
    "Auto-hide judgehosts": "채점 서버 자동 숨김", "Balloon runner": "풍선 배달원", "CID": "CID",
    "Category": "분류", "Change Contest": "대회 변경", "Change editor theme": "에디터 테마 변경",
    "Check new version:": "새 버전 확인:", "Clar answers:": "답변 템플릿:", "Clar categories:": "질문 분류:",
    "Clar default problem queue:": "문제 질문 기본 대기열:", "Clar queues:": "질문 대기열:",
    "Clarification handler": "질의응답 담당자", "Clear all filters": "모든 필터 초기화",
    "Compare script": "비교 스크립트", "Compare script arguments": "비교 스크립트 인자",
    "Compile penalty:": "컴파일 에러 페널티:", "Compiler and runner version overview": "컴파일러/실행기 버전 개요",
    "Compiler version(s)": "컴파일러 버전", "Configuration": "환경설정", "Contest ID": "대회 ID",
    "Contest Stats": "대회 통계", "Create new user": "새 사용자 생성", "Current contests": "현재 대회",
    "Deactivate time:": "비활성화 시각:", "Default compare:": "기본 비교:", "Default full debug:": "기본 전체 디버그:",
    "Default run:": "기본 실행:", "Delayed Judgings (by more than 5s)": "지연된 채점 (5초 이상)",
    "Delete selected": "선택 삭제", "Details": "상세", "Disable Notifications": "알림 끄기",
    "Disable Refresh": "새로고침 끄기", "Disable keyboard shortcuts": "단축키 끄기",
    "Disabled languages": "비활성 언어", "Diskspace error:": "디스크 공간 오류:", "Display": "표시",
    "Display name": "표시 이름", "Don't add user": "사용자 추가 안 함", "Edit all judgehosts": "모든 채점 서버 편집",
    "Edit version command(s)": "버전 명령 편집", "Edit visible judgehosts": "보이는 채점 서버 편집",
    "Email": "이메일", "Enable Notifications": "알림 켜기", "Enable keyboard shortcuts": "단축키 켜기",
    "Enable parallel judging:": "병렬 채점 사용:", "Enable ranking:": "순위 표시 사용:", "Enabled": "사용",
    "Enabled languages": "사용 언어", "End time:": "종료 시각:", "Event feed format:": "이벤트 피드 형식:",
    "Export": "내보내기", "Export YAML": "YAML 내보내기", "Export clarifications": "질의응답 내보내기",
    "Export results": "결과 내보내기", "Export tab-separated": "탭 구분 내보내기", "External ID": "외부 ID",
    "External ccs submission url:": "외부 CCS 제출 URL:", "External contest source critical:": "외부 대회 소스 위험 기준:",
    "External contest sources allow untrusted certificates:": "외부 대회 소스의 신뢰할 수 없는 인증서 허용:",
    "External judgement types:": "외부 채점 유형:", "External systems": "외부 시스템", "File": "파일",
    "Filter on affiliation(s)": "소속으로 필터", "Filter on category(s)": "분류로 필터",
    "Filter on language(s)": "언어로 필터", "Filter on locations(s)": "위치로 필터",
    "Filter on problem(s)": "문제로 필터", "Filter on result(s)": "결과로 필터", "Filter on team(s)": "참가자로 필터",
    "Filter:": "필터:", "Finalize time:": "최종 확정 시각:", "Format": "형식", "Freeze time:": "프리즈 시각:",
    "Full judging": "전체 채점", "Full name": "이름", "General": "일반", "General clarifications": "전체 공지",
    "HTML (display inline)": "HTML (바로 표시)", "HTML (download)": "HTML (다운로드)", "Handled": "처리됨",
    "Handled requests": "처리된 요청", "High contrast (dark)": "고대비 (다크)", "High contrast (light)": "고대비 (라이트)",
    "Honors?": "우수상?", "ICPC ID": "ICPC ID", "ID": "ID", "Icat url:": "Icat URL:", "Import": "가져오기",
    "Import JSON / YAML": "JSON/YAML 가져오기", "Import and export": "가져오기/내보내기",
    "Import archive": "압축 파일 가져오기", "Import contest": "대회 가져오기", "Import problem": "문제 가져오기",
    "Import tab-separated": "탭 구분 가져오기", "Import teams": "참가자 가져오기",
    "Import teams from ICPC CMS": "ICPC CMS에서 참가자 가져오기", "Index": "목차", "Individually ranked?": "개별 순위 산정?",
    "Internal comments (jury viewable only)": "내부 메모 (운영진만 열람)", "Internal errors": "내부 오류",
    "Ip autologin:": "IP 자동 로그인:", "Is the Adminer Database Editor enabled?": "Adminer DB 편집기를 사용할까요?",
    "Is this system running as a shadow system?": "섀도 시스템으로 동작할까요?",
    "Judgehost activated by default:": "채점 서버 기본 활성화:", "Judgehost critical:": "채점 서버 위험 기준:",
    "Judgehost warning:": "채점 서버 경고 기준:", "Keyboard shortcuts": "단축키", "Label": "라벨",
    "Language Stats": "언어별 통계", "Lazy": "지연 평가", "Lazy eval results:": "결과 지연 평가:",
    "Location": "위치", "Memlimit": "메모리 제한", "Memory limit:": "메모리 제한:", "Misery": "Misery",
    "Misery index": "Misery 지수", "Multi-pass limit": "멀티패스 제한", "Name": "이름", "New": "신규",
    "New requests": "새 요청", "No": "아니오", "No balloons": "풍선 없음",
    "No general clarifications.": "전체 공지가 없습니다.", "No new clarification requests.": "새 질문이 없습니다.",
    "No old clarification requests.": "이전 질문이 없습니다.", "No rejudgings defined": "정의된 재채점 없음",
    "Only on request": "요청 시에만", "Organisation": "소속 기관", "Output display limit:": "출력 표시 제한:",
    "Output limit:": "출력 제한:", "Output storage limit:": "출력 저장 제한:", "Outputlimit": "출력 제한",
    "Pause all judgehosts": "모든 채점 서버 일시정지", "Penalty time": "페널티 시간", "Penalty time:": "페널티 시간:",
    "Photo": "사진", "Print clarifications": "질의응답 인쇄", "Print command:": "인쇄 명령:",
    "Problem archive": "문제 압축 파일", "Problem runtime analytics": "문제 실행시간 분석",
    "Problem statement": "문제 지문", "Problems Attempted/Solved": "시도/해결 문제",
    "Process limit:": "프로세스 제한:", "Public description": "공개 설명", "Queue tasks": "대기열 작업",
    "Reset all filters": "모든 필터 초기화", "Reset login status of all team users": "모든 참가자의 로그인 상태 초기화",
    "Results": "결과", "Results prio:": "결과 우선순위:", "Results remap:": "결과 재매핑:", "Roles": "권한",
    "Run script": "실행 스크립트", "Score in seconds:": "초 단위 페널티:", "Scoring": "점수 계산",
    "Script filesize limit:": "스크립트 파일 크기 제한:", "Script memory limit:": "스크립트 메모리 제한:",
    "Script timelimit:": "스크립트 시간 제한:", "Send clarification": "메시지 보내기", "Shadow mode:": "섀도 모드:",
    "Show affiliation logos on the scoreboard?": "순위표에 소속 로고를 표시할까요?", "Show affiliation logos:": "소속 로고 표시:",
    "Show affiliation names in the interfaces?": "화면에 소속을 표시할까요?", "Show affiliations:": "소속 표시:",
    "Show balloons postfreeze:": "프리즈 후 풍선 표시:", "Show compile output in team webinterface?": "참가자 화면에 컴파일 출력을 표시할까요?",
    "Show compile:": "컴파일 결과 표시:", "Show country information in the interfaces?": "화면에 국가 정보를 표시할까요?",
    "Show flags:": "국기 표시:", "Show language versions:": "언어 버전 표시:", "Show limits on team page:": "참가자 페이지에 제한 표시:",
    "Show pending submissions on the scoreboard?": "순위표에 채점 대기 중인 제출을 표시할까요?", "Show pending:": "채점 대기 중 제출 표시:",
    "Show public stats:": "공개 통계 표시:", "Show relative time:": "상대 시간 표시:",
    "Show results of TOO-LATE submissions in team interface?": "참가자 화면에 대회 종료 후 제출의 결과를 표시할까요?",
    "Show sample output:": "예제 출력 표시:", "Show teams on scoreboard:": "순위표에 참가자 표시:",
    "Show teams on the scoreboard?": "순위표에 참가자를 표시할까요?", "Show teams submissions:": "참가자 제출 표시:",
    "Show too late result:": "종료 후 제출 결과 표시:", "Show:": "표시:", "Sort order": "정렬 순서",
    "Source code reader": "소스 코드 열람자", "Sourcefiles limit:": "소스 파일 개수 제한:",
    "Sourcesize limit:": "소스 크기 제한:", "Start all judgehosts": "모든 채점 서버 시작", "Start time:": "시작 시각:",
    "Submissions Over Time": "시간대별 제출", "System": "시스템", "Team column width:": "이름 열 너비:",
    "Team name": "이름", "Teams & groups": "참가자 및 그룹", "Teams from hidden categories": "숨김 분류의 참가자",
    "Teams from visible categories": "공개 분류의 참가자", "The public scoreboard": "공개 순위표",
    "There are no judgings delayed so far.": "현재 지연된 채점이 없습니다.", "Thumbnail size:": "썸네일 크기:",
    "Time format:": "시간 형식:", "Timelimit": "시간 제한", "Timelimit overshoot:": "시간 제한 초과 허용:",
    "Type": "유형", "Types": "유형", "Unfreeze time:": "프리즈 해제 시각:", "Unused executables": "미사용 실행 파일",
    "Used executables": "사용 중 실행 파일", "User": "사용자", "Verification required:": "검증 필요:", "Yes": "예",
    "aborted": "중단됨", "activate": "활성화", "affiliation": "소속", "allow judge": "채점 허용",
    "attempted/solved": "시도/해결", "attempts/solutions": "시도/정답", "category": "분류", "compare": "비교",
    "contest": "대회", "correct": "정답", "country": "국가", "critical": "위험", "deactivate now": "지금 비활성화",
    "email": "이메일", "enabled": "사용", "end": "종료", "executable": "실행 파일", "extensions": "확장자",
    "external ID": "외부 ID", "finalize now": "지금 최종 확정", "function": "함수", "groups": "그룹",
    "hostname": "호스트명", "import-error": "가져오기 오류", "internal error": "내부 오류",
    "judgehost": "채점 서버", "judging": "채점", "kB": "kB", "label": "라벨", "last IP": "최근 IP",
    "last judging": "최근 채점", "limit": "제한", "load (5m/15m/1h/5h)": "부하 (5분/15분/1시간/5시간)",
    "location": "위치", "logo": "로고", "memory": "메모리", "memory limit": "메모리 제한", "name": "이름",
    "never": "안 함", "no": "아니오", "no contest": "대회 없음", "no-output": "출력 없음", "noconn": "연결 없음",
    "ok": "정상", "only on compilation error(s)": "컴파일 오류 시에만", "organization": "소속 기관",
    "organizations": "소속 기관", "output limit": "출력 제한", "pending": "채점 대기 중",
    "preliminary results - not final": "잠정 결과 - 확정 아님", "priority": "우선순위",
    "process balloons?": "풍선 처리?", "public?": "공개?", "queued": "대기 중", "rejudge": "재채점",
    "rejudgings": "재채점", "remaining testcases": "남은 테스트 케이스", "roles": "권한", "run": "실행",
    "run-error": "런타임 에러",
    "compiler-error": "컴파일 에러",
    "memory-limit": "메모리 초과",
    "output-limit": "출력 초과",
    "timelimit": "시간 초과", "scoreboard": "순위표", "scoreboard type": "순위표 유형",
    "self-registered": "자가 등록", "self-registration": "자가 등록", "shortname": "약칭", "shown": "표시됨",
    "sort": "정렬", "start": "시작", "start time": "시작 시각", "stats": "통계", "status": "상태",
    "submissions": "제출", "submitted/correct": "제출/정답", "team priority": "참가자 우선순위", "teams": "참가자",
    "test": "테스트", "time limit": "시간 제한", "type": "유형", "unfreeze now": "지금 프리즈 해제",
    "unjudged": "미채점", "unverified": "미검증", "user": "사용자", "username": "아이디",
    "versions available": "버전 정보 있음", "visible": "공개", "warning": "경고", "wrong-answer": "오답"
  };

  // 숫자·이름 등 가변 값이 섞인 문장은 정규식으로 처리
  var REGEX_RULES = [
    [/^contest over, waiting for results$/, "대회 종료, 결과 대기 중"],
    [/^The scoreboard was frozen with (\d+) minutes? remaining - solutions submitted in the last \d+ minutes? of the contest are still shown as pending\.$/,
      "대회 종료 $1분 전부터 순위표가 프리즈되었습니다. 마지막 $1분 동안의 제출은 채점 대기 중으로 표시됩니다."],
    [/^Last Update: (.+)$/, "마지막 갱신: $1"],
    [/^Submissions for team (.+)$/, "$1의 제출 현황"],
    [/^Submit problem (.+)$/, "$1 제출"],
    [/^Limits: (.+) seconds? \/ (.+) (MB|GB)$/, "제한: $1초 / $2$3"],
    [/^Type: (.+)$/, function (m, p1) {
      var types = p1.split(", ").map(function (t) {
        return DICT[t.trim()] || t.trim();
      });
      return "유형: " + types.join(", ");
    }],
    [/^(.+) problems$/, "$1"],
    [/^Balloons - (.+)$/, "풍선 배달 - $1"],
    [/^# Accepted Submissions: (\d+)$/, "# 정답 제출: $1"],
    [/^# Submissions: (\d+)$/, "# 제출: $1"],
    [/^# of Teams: (\d+)$/, "# 참가자 수: $1"],
    [/^Run (\d+)$/, "실행 $1"],
    [/^(\d+(?: \+ \d+)?) (?:try|tries)$/, "$1회 제출"]
  ];

  function applyRegex(text) {
    for (var i = 0; i < REGEX_RULES.length; i++) {
      var rule = REGEX_RULES[i][0], repl = REGEX_RULES[i][1];
      if (rule.test(text)) {
        return typeof repl === "function" ? text.replace(rule, repl) : text.replace(rule, repl);
      }
    }
    return null;
  }

  function translateNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      var raw = node.nodeValue;
      // 줄바꿈/들여쓰기가 섞인 텍스트도 매칭되도록 공백을 정규화해서 비교
      var t = raw.replace(/\s+/g, " ").trim();
      if (!t) return;
      // 앞뒤 공백은 남긴다. "Problem: <b>A</b>"처럼 뒤에 붙는 값과 띄어 쓰기 위해서다.
      var lead = /^\s/.test(raw) ? " " : "";
      var trail = /\s$/.test(raw) ? " " : "";
      if (DICT.hasOwnProperty(t)) {
        node.nodeValue = lead + DICT[t] + trail;
        return;
      }
      var viaRegex = applyRegex(t);
      if (viaRegex !== null) {
        node.nodeValue = lead + viaRegex + trail;
      }
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    var tag = node.tagName;
    if (tag === "SCRIPT" || tag === "STYLE" || tag === "TEXTAREA" || tag === "CODE" || tag === "PRE") return;
    // 대회 변경 메뉴에는 대회 약칭(test 등)이 그대로 들어간다. 사전 단어와 겹쳐도 번역하지 않는다.
    if (node.id === "navbarDropdownContests" || (node.hasAttribute && node.hasAttribute("data-current-contest"))) return;

    ["placeholder", "title"].forEach(function (attr) {
      var v = node.getAttribute && node.getAttribute(attr);
      if (v && DICT.hasOwnProperty(v.trim())) node.setAttribute(attr, DICT[v.trim()]);
    });
    if ((tag === "INPUT" || tag === "BUTTON") && node.value && DICT.hasOwnProperty(node.value.trim())) {
      node.value = DICT[node.value.trim()];
    }

    for (var i = 0; i < node.childNodes.length; i++) translateNode(node.childNodes[i]);
  }

  function run() {
    translateNode(document.body);
  }

  // jury(운영자) 네비게이션에 "출제 가이드" 링크 삽입 — /jury/guide/ 정적 페이지로 연결
  function injectGuideLink() {
    if (!location.pathname.startsWith("/jury")) return;
    if (document.getElementById("ko-guide-link")) return;
    var scoreLink = [...document.querySelectorAll("a.nav-link")].find(function (a) {
      return a.getAttribute("href") === "/public";
    });
    if (!scoreLink) return;
    var li = document.createElement("li");
    li.className = "nav-item";
    li.id = "ko-guide-link";
    var a = document.createElement("a");
    a.className = "nav-link";
    a.href = "/guide/index.html";
    a.target = "_blank";
    a.rel = "noopener";
    a.innerHTML = '<i class="fas fa-book"></i>출제 가이드';
    li.appendChild(a);
    scoreLink.closest("li").insertAdjacentElement("afterend", li);
  }

  document.addEventListener("DOMContentLoaded", run);
  document.addEventListener("DOMContentLoaded", injectGuideLink);
  // 순위표/제출현황 등 AJAX로 부분 갱신되는 영역 대응 (1초마다 시계·타임스탬프도 갱신되므로 계속 감시)
  //
  // 번역은 nodeValue를 바꾸므로 그 자체가 다시 mutation을 만든다. 감시를 켠 채로 번역하면
  // 번역 -> mutation -> 번역이 끝없이 돌아 jury 표처럼 노드가 많은 화면에서 렌더러가 멈춘다.
  // 그래서 번역하는 동안에는 감시를 끊고, 끝난 뒤에 다시 건다. 한 프레임에 모아서 처리한다.
  var OBSERVE_OPTIONS = { childList: true, subtree: true, characterData: true };
  var pending = [];
  var scheduled = false;

  function startObserving() {
    mo.observe(document.body, OBSERVE_OPTIONS);
  }

  function flush() {
    scheduled = false;
    var batch = pending;
    pending = [];
    mo.disconnect();
    try {
      batch.forEach(function (node) {
        if (node.isConnected) translateNode(node);
      });
    } finally {
      mo.takeRecords();
      startObserving();
    }
  }

  var mo = new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.type === "characterData") {
        pending.push(m.target);
        return;
      }
      m.addedNodes.forEach(function (n) {
        pending.push(n);
      });
    });
    if (pending.length && !scheduled) {
      scheduled = true;
      requestAnimationFrame(flush);
    }
  });
  document.addEventListener("DOMContentLoaded", startObserving);
})();
