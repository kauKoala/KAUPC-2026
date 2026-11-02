# WA 의도: 정답 코드의 range(n-2), range(i+1, n-1) 패턴을 흉내 내다 k의 범위까지 n-1로 줄임
# → 마지막 카드(N번)가 포함된 트리플을 전부 놓침
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
for i in range(n - 2):
    for j in range(i + 1, n - 1):
        for k in range(j + 1, n - 1):        # 버그: n이어야 함
            if is_set(cards[i], cards[j], cards[k]):
                res.append((i+1, j+1, k+1))
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No triple")
