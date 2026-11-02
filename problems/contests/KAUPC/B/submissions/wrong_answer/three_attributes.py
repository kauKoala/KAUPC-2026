# WA 의도: 속성 반복을 range(3)으로 써서 마지막 속성(개수)을 검사하지 않음 (off-by-one)
import sys
input = sys.stdin.readline

def is_set(c1, c2, c3):
    for i in range(3):                       # 버그: 4개 속성 중 3개만 검사
        a, b, c = c1[i], c2[i], c3[i]
        if not ((a == b and b == c) or (a != b and b != c and a != c)):
            return False
    return True

n = int(input())
cards = [input().split() for _ in range(n)]
res = [(i+1, j+1, k+1) for i in range(n) for j in range(i+1, n) for k in range(j+1, n)
       if is_set(cards[i], cards[j], cards[k])]
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No triple")
