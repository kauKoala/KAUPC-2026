# WA 의도: 위와 반대로, 입력 줄 순서를 게임 진행 순서로 착각하고
#          뒤 줄에서 앞 줄 방향으로만 세뇌를 전파한 코드.
#          앞 줄에서 생긴 세뇌가 뒤 줄에 반영되지 않는다.
import sys


def main():
    lines = sys.stdin.read().split("\n")
    n, m = map(int, lines[0].split())

    parent = list(range(n + 1))
    danger = [False] * (n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        parent[rb] = ra
        danger[ra] = danger[ra] or danger[rb]

    mafia_tokens = list(map(int, lines[2].split()))
    mafias = [] if mafia_tokens == [0] else mafia_tokens
    for x in mafias:
        danger[x] = True
    for i in range(1, len(mafias)):
        union(mafias[0], mafias[i])

    turns = [list(map(int, lines[4 + 2 * i].split())) for i in range(m)]

    answer = 0
    for members in reversed(turns):            # 버그: 입력 줄 역순으로 한 방향 전파
        for i in range(1, len(members)):
            union(members[0], members[i])
        if not danger[find(members[0])]:
            answer += 1
    print(answer)


main()
