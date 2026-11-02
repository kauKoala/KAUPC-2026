# 현수막 출력하기

다섯 높이에 따라 3줄짜리 `KKAAUUPPCC` 현수막을 5행 10열로 출력한다.

- 가능한 입력 41개를 모두 넣었다. 40번째는 예제 2(`data/sample/40`)로 옮겼고 나머지 40개는 `data/secret/`에 있다. 생성기는 예제와 같은 입력을 secret에 다시 만들지 않는다.
- 빈 칸은 마침표(`.`)로 출력한다. `output_validators/exact_output/run`이 문자와 마침표의 위치를 정확히 비교한다.
- 정답 풀이는 각 글자 열을 3번씩 고정 크기 캔버스에 기록한다.

검증은 다음처럼 실행한다.

```powershell
python -m unittest discover problems/contests/KAUPC/A/tests -v
python scripts/build-problem.py KAUPC A
```
