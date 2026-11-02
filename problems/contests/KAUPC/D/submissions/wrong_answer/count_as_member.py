# WA 의도: 턴마다 주어지는 참여 인원 P를 참가자 번호로 착각해서 참가자 목록에 함께 넣는다.
# P도 1..N 범위의 수라서, 실제로는 없는 'P번 플레이어'가 그 턴에 참여한 것처럼 처리된다.
# → P번이 위험한 사람이면 안전한 턴을 위험하다고 판정하고, 엉뚱한 사람끼리 이어 세뇌를 퍼뜨린다.
import sys
from collections import deque

lines = sys.stdin.read().split("\n")
n, m = map(int, lines[0].split())
k = int(lines[1])
mafias = [] if k == 0 else list(map(int, lines[2].split()))

adj = [[] for _ in range(n + 1)]
turns = []
for i in range(m):
    p = int(lines[3 + 2 * i])
    members = [p] + list(map(int, lines[4 + 2 * i].split()))   # 버그: P까지 참가자로 넣음
    for j in range(1, len(members)):
        adj[members[0]].append(members[j]); adj[members[j]].append(members[0])
    turns.append(members)
for i in range(1, k):
    adj[mafias[0]].append(mafias[i]); adj[mafias[i]].append(mafias[0])

if k == 0:
    print(m); sys.exit(0)

bad = [False] * (n + 1)
q = deque([mafias[0]]); bad[mafias[0]] = True
while q:
    cur = q.popleft()
    for nb in adj[cur]:
        if not bad[nb]:
            bad[nb] = True; q.append(nb)

print(sum(1 for members in turns if not any(bad[x] for x in members)))
