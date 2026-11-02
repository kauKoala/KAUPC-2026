# WA 의도: 트리플이 없을 때 문구를 "No Triple"(대문자 T)로 출력
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
res = [(i+1, j+1, k+1) for i in range(n) for j in range(i+1, n) for k in range(j+1, n)
       if is_set(cards[i], cards[j], cards[k])]
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No Triple")   # 버그: 대소문자
