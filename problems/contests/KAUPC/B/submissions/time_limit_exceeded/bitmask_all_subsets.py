# TLE 의도: 2^N개의 모든 부분집합을 비트마스크로 돌며 원소가 3개인 것만 검사
# N이 작으면(≈20 이하) 정답이지만 N=81이면 2^81 → 시간 초과
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
for mask in range(1 << n):
    if bin(mask).count("1") != 3:
        continue
    idx = [i for i in range(n) if mask >> i & 1]
    if is_set(cards[idx[0]], cards[idx[1]], cards[idx[2]]):
        res.append(tuple(x + 1 for x in idx))
res.sort()   # 비트마스크 순서는 사전순이 아니므로 정렬
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No triple")
