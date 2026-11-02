# 다리 추가하기

이 폴더의 지문, 생성기, 데이터, 정답·오답 코드를 함께 수정한다.

## 제한과 의도

`N ≤ 300`, `M ≤ 50,000`, `M < N²`, `Q ≤ 1,000`이다. 1번 쿼리 수에는 따로 제한이 없다. 쿼리마다 힙 다익스트라를 실행하는 풀이가 기준 정답이다. 시간 제한은 5초다.

`submissions/accepted/`에는 C++, Java, PyPy 정답 코드가 있고, `wrong_answer/`와 `time_limit_exceeded/`에는 판정 확인용 코드가 있다.

## 테스트

```powershell
python -m unittest discover .\problems\contests\KAUPC\G\tests -v
python .\problems\contests\KAUPC\G\generators\generate_tests.py
```

생성기는 결정론적으로 `data/`의 이름 있는 케이스를 갱신한다. 모든 입력은 선언한 줄 수, 정점·가중치 범위, `M < N²`, 쿼리·갱신 수를 테스트로 검사한다.

최대 크기 케이스는 `max-dijkstra-queries`, `max-dijkstra-updates`, `max-parallel-edges`다. 작은 정점에 간선이 많은 `small-edge-heavy`, 단절·중복 간선·자기 루프·반복 갱신도 포함한다.

`scripts/build-problem.ps1 KAUPC G`가 DOMjudge ZIP을 만든다.

## 운영 서버 제출 검증 (2026-10-29)

1번 쿼리 500개 제한을 없애고 `max-updates`를 추가한 뒤 저장소의 제출 코드를 그대로 다시 제출했다. 판정은 변경 전과 모두 같다. 운영 서버의 24개 테스트케이스에 대한 판정이며, 시간은 테스트케이스별 최대 CPU 시간이다. Python은 PyPy 3다.

| 원본 코드 | 판정 | 최대 CPU | 제출 |
| --- | --- | --- | --- |
| `submissions/accepted/DijkstraPerQuery.java` | AC | 1.845초 | [#212](https://kaupc2026.me/jury/submissions/212) |
| `submissions/accepted/Main.java` | AC | 0.705초 | [#214](https://kaupc2026.me/jury/submissions/214) |
| `submissions/accepted/dijkstra_heap_python.py` | AC | 0.726초 | [#216](https://kaupc2026.me/jury/submissions/216) |
| `submissions/accepted/dijkstra_per_query.cpp` | AC | 0.131초 | [#218](https://kaupc2026.me/jury/submissions/218) |
| `submissions/accepted/dijkstra_python.py` | AC | 1.380초 | [#220](https://kaupc2026.me/jury/submissions/220) |
| `submissions/accepted/floyd_python.py` | AC | 1.691초 | [#222](https://kaupc2026.me/jury/submissions/222) |
| `submissions/accepted/solution.c` | AC | 0.146초 | [#224](https://kaupc2026.me/jury/submissions/224) |
| `submissions/accepted/solution.cpp` | AC | 0.162초 | [#226](https://kaupc2026.me/jury/submissions/226) |
| `submissions/time_limit_exceeded/floyd_every_query.cpp` | TLE | 5.536초 | [#228](https://kaupc2026.me/jury/submissions/228) |
| `submissions/wrong_answer/directed_edges.c` | WA | 0.033초 | [#229](https://kaupc2026.me/jury/submissions/229) |
| `submissions/wrong_answer/last_edge_weight.c` | WA | 0.044초 | [#230](https://kaupc2026.me/jury/submissions/230) |
