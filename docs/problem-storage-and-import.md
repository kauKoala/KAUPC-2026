# 문제 원본과 DOMjudge DB의 경계

## 단일 원본은 저장소다

문제의 원본은 하나다. 예를 들어 A번 문제는 `problems/contests/KAUPC/A/`에 둔다.

- `problem_statement/problem.html`: 참가자에게 보이는 지문
- `data/sample/`, `data/secret/`: 입력과 정답 파일
- `submissions/accepted/`: 정답 코드. `wrong_answer/`, `time_limit_exceeded/`에는 걸러져야 하는 풀이
- `generators/generate_tests.py`: 테스트를 다시 만들 수 있는 결정론적 생성기
- `problem.yaml`, `domjudge-problem.ini`: DOMjudge 메타데이터

DOMjudge DB는 이 파일들에서 언제든 다시 만들 수 있는 **사본**이다. DB만 가진 것은 커밋되지 않고, 다른 PC에서 clone해도 보이지 않으며, 볼륨을 지우면 사라진다.

`build/problem.zip`은 생성물이므로 Git에 넣지 않는다.

TEST에서 KAUPC 문제를 함께 쓰려면 `problems/contests/TEST/C/source.txt`에 원본 경로(`../KAUPC/F`)를 적는다. 파일을 복제하지 않고 같은 문제 레코드를 TEST 대회에 라벨만 달리해 연결한다.

## 문제를 추가하는 두 가지 방법

둘 다 결과물은 같다. `problems/contests/` 아래 파일이다.

### 코드로

```powershell
.\scripts\new-problem.ps1 -Contest KAUPC -Label C -ProblemId myproblem -Name "문제 이름"
```

템플릿이 복사되고 치환자가 채워지며 대회의 `problems.yaml`에 항목이 추가된다. 이후 지문·정답 코드·생성기를 채운다.

### 웹으로

`docker compose up -d` 뒤 <http://127.0.0.1:8088> 을 연다. jury 화면 상단 메뉴의 "문제 에디터" 링크로도 갈 수 있다.

- 문제 목록은 DB가 아니라 파일에서 읽는다
- "템플릿으로 생성"은 `scripts/new-problem.py`를 그대로 호출한다
- 지문 편집, 테스트 `.in`/`.ans` 업로드·삭제, 제출 코드 업로드가 된다
- 저장하면 즉시 저장소 파일이 바뀐다. DB는 건드리지 않는다

에디터는 인증이 없다. compose가 `127.0.0.1`에만 바인딩하므로 이 PC 밖에서는 접근할 수 없다.

### DOMjudge jury UI로는 만들지 않는다

jury UI에서 문제를 만들면 DB에만 생기고 저장소에는 아무것도 남지 않는다. 대회 운영(리저지, 클라 응답, 스코어보드)에만 쓴다.

## Docker Compose가 하는 일

`docker compose up -d` 뒤 provisioner가 다음을 수행한다.

1. `contest.yaml`로 대회를 만든다(이미 있으면 건너뛴다)
2. 대회에 아직 없는 문제는 `problems.yaml`에서 **그 문제 블록만** 뽑아 등록한다
3. 파일 쪽 테스트 집합이 DB와 다르면 DB 쪽 테스트를 `deleted` 처리한 뒤 다시 넣는다. 지우지 않고 재import하면 DOMjudge가 `rankindex` 중복으로 실패한다
4. 패키지를 ZIP으로 묶어 지문·테스트·메타데이터를 등록한다
5. `source.txt`가 있는 폴더는 원본 문제를 그 대회에 라벨만 달아 연결한다

즉 **파일을 고치고 `docker compose up -d provisioner`를 돌리면 DB가 파일을 따라온다.**

메타데이터 파일이 CRLF로 저장되면 문제 id에 캐리지 리턴이 섞여 등록이 깨진다. `.gitattributes`가 `problems/**`와 `bootstrap/*.sh`를 LF로 고정하고, provisioner도 방어적으로 `\r`를 떼어낸다.

## 동기화 확인

```powershell
python .\scripts\check-sync.py
```

저장소와 DB의 문제 집합을 비교한다. DB에만 있는 문제(=jury UI로 만든 것)가 있으면 종료 코드 1로 실패한다. 저장소에만 있으면 provisioner를 돌리라고 알려준다.

## 새 PC에서 재현

```powershell
git clone <저장소>
cd oj-domjudge
docker compose up -d
```

DB는 비어 있어도 된다. provisioner가 저장소 상태 그대로 대회·문제·테스트를 만든다.
