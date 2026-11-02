# 문제 패키지 규칙

- 문제의 유일한 원본은 `problems/contests/<대표 대회>/<라벨>/`이다. DOMjudge DB와 `build/problem.zip`은 저장소에서 다시 만들 수 있는 사본이다.
- DOMjudge jury UI로 문제를 만들지 않는다. DB에만 생겨서 커밋되지 않는다. 웹에서 만들려면 문제 에디터(<http://127.0.0.1:8088>)를 쓴다. 에디터는 DB가 아니라 저장소 파일을 쓴다.
- 새 문제는 `scripts/new-problem.ps1 -Contest <대회> -Label <라벨> -ProblemId <id> -Name "<이름>"`으로 시작한다. 템플릿 복사와 `problems.yaml` 항목 추가까지 해 준다.
- 같은 문제를 다른 대회에서도 쓸 때는 `<다른 대회>/<라벨>/source.txt`로 원본 폴더를 가리킨다. 문제 파일을 복제하지 않는다.
- 문제를 변경하면 `python -m unittest discover problems/contests/<대표 대회>/<라벨>/tests -v`와 생성기를 실행한다.
- 테스트 데이터는 최대 크기·중간 크기·경계 케이스를 모두 둔다. 정답 코드뿐 아니라 `submissions/wrong_answer/`와 `submissions/time_limit_exceeded/`도 함께 커밋해, 데이터가 실제로 거르는지 확인할 수 있게 한다.
- 제한 시간은 `domjudge/judgehost:latest` 컨테이너에서 재보고 README에 실측치를 남긴다. 정답이 제한의 1/5 안쪽, 비효율 풀이가 제한의 3배 밖이면 충분하다.
- 저장소의 텍스트 파일은 LF로 저장한다. CRLF가 섞이면 provisioner가 문제 id를 잘못 읽는다. `.gitattributes`가 `problems/**`와 `bootstrap/*.sh`를 고정한다.
- `scripts/build-problem.ps1 <대표 대회> <라벨>`은 해당 원본에서 `build/problem.zip`을 만든다. Compose provisioner가 이를 자동 등록한다.
- 파일을 고친 뒤에는 `docker compose up -d provisioner`로 DB를 따라오게 하고, `python scripts/check-sync.py`로 저장소와 DB가 같은 문제 집합인지 확인한다.
- custom checker가 필요하면 source, build, run 파일을 문제 폴더에 함께 커밋한다.
- 비밀값, DOMjudge 관리자 비밀번호, AWS 자격 증명은 저장소에 커밋하지 않는다.
