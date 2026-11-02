# WA 의도: "모두 다름" 판정에서 a != c 비교를 빠뜨림
# → (X, Y, X) 패턴(첫째와 셋째만 같음)을 "모두 다름"으로 잘못 인정
import sys
input = sys.stdin.readline

def is_set(c1, c2, c3):
    for i in range(4):
        a, b, c = c1[i], c2[i], c3[i]
        if not ((a == b and b == c) or (a != b and b != c)):   # 버그: a != c 누락
            return False
    return True

n = int(input())
cards = [input().split() for _ in range(n)]
res = [(i+1, j+1, k+1) for i in range(n) for j in range(i+1, n) for k in range(j+1, n)
       if is_set(cards[i], cards[j], cards[k])]
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No triple")
