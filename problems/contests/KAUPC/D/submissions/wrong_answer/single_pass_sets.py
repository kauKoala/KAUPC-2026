# WA 의도: 집합 하나로 입력 줄을 한 번만 훑으며 세뇌를 전파.
#          아직 세뇌되지 않은 시민들끼리 먼저 만난 턴을 기억하지 못해서,
#          그중 한 명이 뒤 줄에서 세뇌돼도 나머지에게 번지지 않는다.
import sys

lines = sys.stdin.read().split("\n")
n, m = map(int, lines[0].split())
mafia_tokens = list(map(int, lines[2].split()))
mafias = [] if mafia_tokens == [0] else mafia_tokens

turns = [list(map(int, lines[4 + 2 * i].split())) for i in range(m)]

bad = set(mafias)
for members in turns:                          # 버그: 단일 패스 + 집합 전파
    if bad & set(members):
        bad |= set(members)

print(sum(1 for members in turns if not (bad & set(members))))
