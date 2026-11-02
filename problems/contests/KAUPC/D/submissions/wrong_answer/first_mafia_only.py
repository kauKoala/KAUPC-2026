# WA 의도: 마피아가 여러 명일 때 첫 번째 마피아만 기준으로 오염을 계산
#          (마피아끼리 잇는 간선을 빼먹음) → 다른 마피아와만 접촉한 턴을 놓침
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
# 버그: 마피아들끼리 잇는 간선이 없음

if cnt == 0:
    print(m); sys.exit(0)

bad = [False] * (n + 1)
q = deque([mafias[0]]); bad[mafias[0]] = True
while q:
    cur = q.popleft()
    for nb in adj[cur]:
        if not bad[nb]:
            bad[nb] = True; q.append(nb)
print(sum(1 for members in turns if not any(bad[x] for x in members)))
