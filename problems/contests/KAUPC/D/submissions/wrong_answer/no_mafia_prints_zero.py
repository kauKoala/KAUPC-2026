# WA 의도: 마피아 수가 0인 입력("0"만 있는 줄)에서 0을 출력
# → 마피아가 없으면 모든 턴에서 특종 가능(M)인데 0으로 처리
import sys
from collections import deque

lines = sys.stdin.read().split("\n")
n, m = map(int, lines[0].split())
mafia_tokens = list(map(int, lines[2].split()))
mafias = [] if mafia_tokens == [0] else mafia_tokens
cnt = len(mafias)

turns = []
adj = [[] for _ in range(n + 1)]
for i in range(m):
    members = list(map(int, lines[4 + 2 * i].split()))
    for j in range(1, len(members)):
        adj[members[0]].append(members[j]); adj[members[j]].append(members[0])
    turns.append(members)
for i in range(1, cnt):
    adj[mafias[0]].append(mafias[i]); adj[mafias[i]].append(mafias[0])

if cnt == 0:
    print(0)                              # 버그: m 이어야 함
    sys.exit(0)

bad = [False] * (n + 1)
q = deque([mafias[0]]); bad[mafias[0]] = True
while q:
    cur = q.popleft()
    for nb in adj[cur]:
        if not bad[nb]:
            bad[nb] = True; q.append(nb)
print(sum(1 for members in turns if not any(bad[x] for x in members)))
