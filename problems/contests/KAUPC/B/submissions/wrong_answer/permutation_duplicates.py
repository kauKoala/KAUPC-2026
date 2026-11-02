# WA 의도: 조합이 아닌 순열로 3장을 고름 (j, k를 0부터 다시 돌림)
# → 같은 트리플을 순서만 바꿔 여러 번 출력 (1 2 3, 1 3 2, 2 1 3 ...)
import sys
input = sys.stdin.readline

def is_set(c1, c2, c3):
    for i in range(4):
        a, b, c = c1[i], c2[i], c3[i]
        if not ((a == b and b == c) or (a != b and b != c and a != c)):
            return False
    return True

n = int(input())
cards = [input().split() for _ in range(n)]
res = []
for i in range(n):
    for j in range(n):
        for k in range(n):
            if i != j and j != k and i != k and is_set(cards[i], cards[j], cards[k]):
                res.append((i+1, j+1, k+1))
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No triple")
