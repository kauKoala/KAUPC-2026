# 디스코드 봇 유지보수

이 폴더가 문제의 원본이다. TEST/C는 `source.txt`로 이 폴더를 공유한다.

## 규칙과 풀이

작업은 `feat`, `fix`, `hotfix`, `deprecate`, `issue` 다섯 가지다. 시간 제한은 2초, 메모리 제한은 512MB다.

최소 힙에는 `(사용 지수, 이름)`을 넣고, 해시맵에는 살아 있는 기능의 현재 사용 지수를 저장한다. 값을 갱신할 때는 새 항목을 힙에 넣고, 삭제할 때는 맵에서만 지운다. 조회 시 힙의 이름이 맵에 없거나 현재 값이 다르면 오래된 항목이므로 버린다. 같은 사용 지수에서는 이름 사전순으로 고른다.

최대 힙은 필요 없다. 전체 시간 복잡도는 `O(X log X)`, 공간 복잡도는 `O(X)`다. 이름별 상태는 삭제 후 재등록을 포함해 관리해야 한다.

## 검증

- C, C++, Java, Python 정답 코드는 같은 다섯 연산을 구현한다.
- 300개 무작위 소형 입력을 독립적인 단순 시뮬레이션과 비교한다.
- 모든 입력의 연산 종류, 인자 개수, 작업 수, 최소 한 번의 `issue`를 검사한다.
- 예제 2는 사전순 동률, 지정 갱신, 삭제 후 재등록, 최저 기능 갱신을 다룬다.
- `max-random`, `max-fix`는 각각 20만 작업이다. 다른 데이터는 빈 상태, 중복 추가, 긴 이름, 64비트 누적, 잦은 갱신과 삭제를 포함한다.
- `wrong_answer/`의 세 풀이는 동률 무시, 중복 추가 덮어쓰기, 오래된 힙 항목 처리 누락을 검사한다.
- `time_limit_exceeded/`에는 매번 전체 정렬하는 Python과 전체 순회하는 Java 풀이가 있다.

## 데이터 재생성

`python generators/generate_tests.py`로 기본 데이터를 만든다. `generators/seeds.txt`에 기록한 시드 데이터도 `generators/gen.py`로 생성한다. 생성한 입력의 답은 `submissions/accepted/solution.py`로 계산한다.

검증 명령: `python -m unittest discover problems/contests/KAUPC/F/tests -v`

문제는 출력이 유일하므로 custom checker를 사용하지 않는다. 측정 결과는 아래에 기록한다.

## 운영 서버 제출 검증 (2026-10-29)

기능 이름을 영어 소문자로 바꾸고 `p ≤ 10,000`으로 줄여 데이터를 다시 만든 뒤 저장소의 제출 코드를 그대로 다시 제출했다. 판정은 모두 의도대로다. 운영 서버의 27개 테스트케이스에 대한 판정이며, 시간은 테스트케이스별 최대 CPU 시간이다. Python은 PyPy 3다.

| 원본 코드 | 판정 | 최대 CPU | 제출 |
| --- | --- | --- | --- |
| `submissions/accepted/Main.java` | AC | 0.508초 | [#232](https://kaupc2026.me/jury/submissions/232) |
| `submissions/accepted/alt_solution.cpp` | AC | 0.216초 | [#233](https://kaupc2026.me/jury/submissions/233) |
| `submissions/accepted/solution.c` | AC | 0.090초 | [#234](https://kaupc2026.me/jury/submissions/234) |
| `submissions/accepted/solution.cpp` | AC | 0.156초 | [#235](https://kaupc2026.me/jury/submissions/235) |
| `submissions/accepted/solution.py` | AC | 0.462초 | [#236](https://kaupc2026.me/jury/submissions/236) |
| `submissions/time_limit_exceeded/SortEveryIssue.java` | TLE | 3.004초 | [#237](https://kaupc2026.me/jury/submissions/237) |
| `submissions/time_limit_exceeded/sort_every_issue.py` | TLE | 2.995초 | [#238](https://kaupc2026.me/jury/submissions/238) |
| `submissions/wrong_answer/feat_overwrites.py` | WA | 0.345초 | [#239](https://kaupc2026.me/jury/submissions/239) |
| `submissions/wrong_answer/no_tie_break.py` | WA | 0.399초 | [#240](https://kaupc2026.me/jury/submissions/240) |
| `submissions/wrong_answer/stale_by_name_only.py` | WA | 0.041초 | [#241](https://kaupc2026.me/jury/submissions/241) |

시간 제한 2초를 유지한다. 언어별 시간 배율은 변경하지 않았다. 로컬 측정이나 단독 실행의 경과 시간으로 운영 판정을 대신하지 않는다.
