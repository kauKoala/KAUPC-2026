# WA 의도: 마피아끼리만 그래프로 잇고 턴 참가자는 잇지 않음
# → 사실상 "마피아가 직접 들어간 턴"만 제외하는 것과 같아짐 + 마피아 전파도 틀림
import sys
from collections import deque

lines = sys.stdin.read().split("\n")
n, m = map(int, lines[0].split())
mafia_tokens = list(map(int, lines[2].split()))
mafias = [] if mafia_tokens == [0] else mafia_tokens
cnt = len(mafias)

adj = [[] for _ in range(n + 1)]
for i in range(1, cnt):                   # 버그: 턴 간선 추가 누락
    adj[mafias[0]].append(mafias[i])
    adj[mafias[i]].append(mafias[0])

turns = [list(map(int, lines[4 + 2 * i].split())) for i in range(m)]

bad = [False] * (n + 1)
if cnt:
    q = deque([mafias[0]]); bad[mafias[0]] = True
    while q:
        cur = q.popleft()
        for nb in adj[cur]:
            if not bad[nb]:
                bad[nb] = True; q.append(nb)

print(sum(1 for members in turns if not any(bad[x] for x in members)))
