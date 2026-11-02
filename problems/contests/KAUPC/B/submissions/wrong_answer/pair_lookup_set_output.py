# WA 의도: O(N^2) "세 번째 카드 역산" 풀이를 쓰면서 중복 제거를 set으로 하고
#          set을 정렬하지 않고 그대로 출력 → 줄 순서가 해시 순서가 됨
import sys

data = sys.stdin.read().split()
n = int(data[0])
cards = [tuple(data[1 + 4*i: 5 + 4*i]) for i in range(n)]
domains = [("마름모", "타원", "물결"), ("채움", "테두리", "빗금"),
           ("빨강", "보라", "초록"), ("1개", "2개", "3개")]
pos = {c: i for i, c in enumerate(cards)}

found = set()
for i in range(n):
    for j in range(i + 1, n):
        third = tuple(cards[i][a] if cards[i][a] == cards[j][a]
                      else next(v for v in domains[a] if v not in (cards[i][a], cards[j][a]))
                      for a in range(4))
        k = pos.get(third)
        if k is not None and k != i and k != j:
            found.add(tuple(sorted((i + 1, j + 1, k + 1))))

if found:
    for t in found:                          # 버그: sorted(found)여야 함
        print(*t)
else:
    print("No triple")
