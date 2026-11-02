# TLE 의도: "넣는다/안 넣는다" 재귀로 조합을 만들되, 3장을 다 고른 뒤에도 가지치기를 하지 않음
# → 탐색 노드 수가 2^N. 결과는 맞지만 N이 크면 시간 초과
import sys
sys.setrecursionlimit(10000)
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
picked = []

def go(idx):
    if idx == n:
        if len(picked) == 3 and is_set(*(cards[p] for p in picked)):
            res.append(tuple(p + 1 for p in picked))
        return
    # 버그: len(picked) > 3 이어도 계속 내려감 (가지치기 없음)
    picked.append(idx)
    go(idx + 1)
    picked.pop()
    go(idx + 1)

go(0)
res.sort()
print("\n".join(f"{a} {b} {c}" for a, b, c in res) if res else "No triple")
