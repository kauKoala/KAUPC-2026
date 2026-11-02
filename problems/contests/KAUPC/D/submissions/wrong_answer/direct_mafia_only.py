# WA 의도: 전파를 전혀 하지 않고, 마피아가 '직접' 참여한 턴만 제외
# → 마피아와 접촉한 시민이 낀 턴을 걸러내지 못함
import sys

lines = sys.stdin.read().split("\n")
n, m = map(int, lines[0].split())
mafia_tokens = list(map(int, lines[2].split()))
mafias = set() if mafia_tokens == [0] else set(mafia_tokens)

answer = 0
for i in range(m):
    members = list(map(int, lines[4 + 2 * i].split()))
    if not (mafias & set(members)):      # 버그: 간접 접촉 무시
        answer += 1
print(answer)
