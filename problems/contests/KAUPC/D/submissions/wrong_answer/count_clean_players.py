# WA 의도: 특종 가능한 '턴 수'가 아니라 안전한 '플레이어 수'를 출력
import sys
from collections import deque

lines = sys.stdin.read().split("\n")
n, m = map(int, lines[0].split())
mafia_tokens = list(map(int, lines[2].split()))
mafias = [] if mafia_tokens == [0] else mafia_tokens
cnt = len(mafias)

adj = [[] for _ in range(n + 1)]
turns = []
for i in range(m):
    members = list(map(int, lines[4 + 2 * i].split()))
    for j in range(1, len(members)):
        adj[members[0]].append(members[j]); adj[members[j]].append(members[0])
    turns.append(members)
for i in range(1, cnt):
    adj[mafias[0]].append(mafias[i]); adj[mafias[i]].append(mafias[0])

bad = [False] * (n + 1)
if cnt:
    q = deque([mafias[0]]); bad[mafias[0]] = True
    while q:
        cur = q.popleft()
        for nb in adj[cur]:
            if not bad[nb]:
                bad[nb] = True; q.append(nb)

safe = set()
for members in turns:
    if not any(bad[x] for x in members):
        safe |= set(members)
print(len(safe))                          # 버그: 턴 수가 아니라 사람 수
