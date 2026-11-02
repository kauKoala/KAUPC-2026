# WA 의도: 마피아와 '직접 같은 턴'에 있던 시민까지만 오염으로 보고, 그 다음 단계는 전파하지 않음
# → 사슬처럼 이어진 접촉(A-마피아, B-A, C-B ...)을 놓침
import sys

lines = sys.stdin.read().split("\n")
n, m = map(int, lines[0].split())
mafia_tokens = list(map(int, lines[2].split()))
mafias = [] if mafia_tokens == [0] else mafia_tokens

turns = [list(map(int, lines[4 + 2 * i].split())) for i in range(m)]

bad = set(mafias)
for members in turns:                     # 버그: 한 번만 훑고 끝 (고정점까지 반복하지 않음)
    if set(mafias) & set(members):
        bad |= set(members)

print(sum(1 for members in turns if not (bad & set(members))))
