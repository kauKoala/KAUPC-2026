# WA 의도: 바깥 루프를 가장 큰 번호 k로 돌림 → 각 줄은 오름차순이지만
#          줄 순서가 "첫 번째 번호 기준 사전순"이 아니라 "마지막 번호 기준"이 됨
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
for k in range(n):
    for j in range(k):
        for i in range(j):
            if is_set(cards[i], cards[j], cards[k]):
                res.append((i+1, j+1, k+1))
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No triple")
