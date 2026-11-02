# DOMjudge 문제 템플릿

문제의 **유일한 원본은 이 저장소**다. DOMjudge DB는 저장소에서 다시 만들 수 있는 사본이므로, 웹 jury UI로 문제를 만들지 않는다. 웹에서 만든 문제는 커밋되지 않고 다른 PC에서도 보이지 않는다.

## 새 문제 만들기

```powershell
.\scripts\new-problem.ps1 -Contest KAUPC -Label C -ProblemId myproblem -Name "문제 이름"
```

스크립트가 이 폴더를 `problems/contests/<대회>/<라벨>/`로 복사하고, 치환자를 채우고, 대회의 `problems.yaml`에 항목을 추가한다. 손으로 만들려면 아래 치환자를 직접 바꾼다.

| 치환자 | 예 |
| --- | --- |
| `간식(hard)` | 디스코드 봇 유지보수 |
| `dessert2` | botmaintenance |
| `KAUPC` | KAUPC |
| `K` | C |
| `KAUPC2026` | KAUPC2026 |

## 채우는 순서

1. `problem_statement/problem.html` — 지문, 제한, 예제. 예제는 `data/sample/1.*`와 글자까지 같아야 한다
2. `submissions/accepted/` — 정답 코드. 채점 환경과 같은 언어로 최소 하나, 가능하면 C·자바·파이썬
3. `generators/gen.py` — 시드 하나를 받아 입력 하나를 출력하도록 고친다
4. 에디터의 "generator로 생성"에 시드를 넣으면 `data/`에 `.in`·`.ans`가 생긴다
5. `submissions/wrong_answer/`, `submissions/time_limit_exceeded/` — 흔한 오답과 비효율 풀이. 이게 있어야 테스트 데이터가 실제로 거르는지 확인된다
6. `python -m unittest discover tests -v`
7. `docker compose up -d` → provisioner가 등록

## 제한 시간 정하기

채점 환경과 같은 컨테이너에서 재보고, README에 실측치를 남긴다.

```powershell
docker run --rm -v "${PWD}:/w:ro" --entrypoint sh domjudge/judgehost:latest -c "python3 /w/..."
```

정답 코드가 제한의 1/5 안쪽, 비효율 풀이가 제한의 3배 밖이면 충분하다.

## 파일 규칙

- 모든 텍스트 파일은 **LF**로 저장한다. CRLF가 섞이면 provisioner가 문제 id를 잘못 읽는다(`.gitattributes`가 막아준다)
- `build/problem.zip`은 생성물이므로 커밋하지 않는다
- custom checker가 필요하면 source·build·run 파일을 이 폴더에 함께 커밋한다
