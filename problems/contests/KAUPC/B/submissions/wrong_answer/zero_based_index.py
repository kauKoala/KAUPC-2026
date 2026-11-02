# WA 의도: 카드 번호를 0번부터 출력 (+1 누락)
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
res = [(i, j, k) for i in range(n) for j in range(i+1, n) for k in range(j+1, n)
       if is_set(cards[i], cards[j], cards[k])]
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No triple")
