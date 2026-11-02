# 출제진 가이드 — 문제 업로드 & 대회 세팅

DOMjudge 주소: https://passion-meaningful-lance-earnings.trycloudflare.com/ (또는 http://localhost:12345/)
(트콘 서버가 켜져 있을 때만 유효 — 바뀌면 담당자에게 새 주소 요청)

## 1. 계정 받기

관리자(팀장)가 **Admin → Users → Add new user** 에서 만들어줍니다. 출제만 할 사람은:

- Roles: **Jury User** 체크 (문제/채점 관리 가능, 대회 설정은 못 건드림)
- Team: 없음 (`-- no team --`)
- 계정 정보(아이디/비번) 받으면 로그인

## 2. 문제 만들기 — 두 가지 방법

### 방법 A. 웹 UI로 직접 (권장, 별도 도구 불필요)

1. **Jury → Problems → Add new problem**
   - Name, Timelimit(초), 문제 유형(Type: 보통 `pass-fail`, 정답이 여러 개면 `scoring`, 인터랙티브면 `interactive`) 입력 후 저장
2. 저장된 문제 페이지에서 **Testcases → edit**
   - 테스트케이스마다 입력파일(`.in`)과 정답파일(`.ans`) 업로드
   - "Sample" 체크하면 참가자에게 공개되는 예제로 표시됨 (보통 1~2개만 sample, 나머지는 secret)
3. 문제 지문(PDF/HTML)은 문제 페이지 하단 **Attachments → Add** 로 업로드
   (지문 PDF 안에 시간제한/메모리제한/입출력 형식은 사람이 직접 적어야 함 — 웹 UI 필드와 별개)
4. 스페셜 저지(정답이 여러 개, 실수 오차 허용 등)가 필요하면 **Compare script**를 `default` 대신 커스텀으로 지정 — 이 경우 아래 방법 B 참고

### 방법 B. zip 패키지로 만들어서 Import (고급, 채점기 커스텀 필요할 때)

로컬에서 폴더 구조를 만들고 zip으로 압축 후 **Jury → Problems → Import problem** 에 업로드:

```
문제이름/
├── problem.yaml              # name, timelimit 등 메타데이터
├── domjudge-problem.ini      # (선택) 문제 외부ID, 색상 등
├── problem_statement/
│   └── problem.en.tex        # 또는 problem.pdf
├── data/
│   ├── sample/
│   │   ├── 1.in
│   │   └── 1.ans
│   └── secret/
│       ├── 1.in
│       ├── 1.ans
│       ├── 2.in
│       └── 2.ans
└── output_validators/        # special judge 쓸 때만
    └── checker.cpp           # ICPC/testlib 스타일 checker
```

`problem.yaml` 최소 예시:

```yaml
name: 'Hello World'
timelimit: 1
```

기존 예제(Demo contest의 hello / fltcmp / boolfind)를 **Jury → Problems → 문제 클릭 → Export** 로 내려받으면
실제 동작하는 zip 구조를 그대로 참고할 수 있습니다 (fltcmp는 실수 오차 허용 비교, boolfind는 인터랙티브 채점 예시라
특수채점 만들 때 특히 유용).

## 3. 업로드 후 확인 (필수)

1. 본인 계정으로 실제 정답 코드 한 번 제출해서 **Correct** 뜨는지 확인
2. 일부러 오답/시간초과 코드도 제출해서 **Wrong Answer / Time Limit** 이 제대로 뜨는지 확인
   (judgehost가 살아있어야 채점됨 — `docker compose ps` 로 `judgehost` 컨테이너 `Up` 상태 확인)

## 4. 대회(Contest) 세팅 — 관리자용

**Jury → Contests → Add contest** (또는 지금 있는 `demo` 대회를 이름만 바꿔 재사용)

- Name / Shortname, 시작시간, 진행시간(4~5시간)
- Problems 탭에서 방금 만든 문제들을 순서대로 연결, 배점(letter A/B/C...)과 balloon 색상 지정
- Freeze time(순위표 프리즈 시각, 보통 종료 1시간 전) 설정 권장

문제/테스트케이스는 대회 시작 전까지 언제든 수정 가능하지만, **대회 시작 후 테스트케이스 변경은 이미 채점된 제출에는 소급 반영 안 됨** — 반드시 시작 전에 방법 3(업로드 후 확인)까지 끝내둘 것.
