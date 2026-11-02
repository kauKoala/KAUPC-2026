import sys
input = sys.stdin.readline
from collections import deque

# 너비 우선 탐색
def bfs(start, graph) :
    queue = deque()
    visited = [False] * (n+1)
    queue.append(start)
    visited[start] = True

    while queue :
        node = queue.popleft()
        for neighboor in graph[node] :
            if not visited[neighboor] :
                queue.append(neighboor)
                visited[neighboor] = True

    return visited


# 입력처리
n, m = map(int, input().split())
mafia_num = int(input())
mafia = list(map(int, input().split()))      # 마피아가 0명이면 이 줄은 "0" 하나다

# 그래프 만들기(마피아들을 간선으로 잇는다)
# 그래프는 결국 탐색하다 보면 연결된 모든 이웃을 방문하게 되므로,
# 한 턴 내에서 간선을 한 번 씩만 그어준다.
users = {i:[] for i in range(n+1)}
for i in range(mafia_num - 1) :
    users[mafia[i]].append(mafia[i+1])
    users[mafia[i+1]].append(mafia[i])

# 입력처리
turns = []
for _ in range(m) :
    turn_num = int(input())                  # 참여 플레이어 수 P
    turns.append(list(map(int, input().split())))

for i in range(m) :
    turn = turns[i]
    turn_num = len(turn)

    # 시민이 마피아와 함께 턴을 보내는 경우
    for j in range(turn_num - 1) :
        if turn[j+1] not in users[turn[j]] :
            users[turn[j]].append(turn[j+1])
            users[turn[j+1]].append(turn[j])

# 시작 노드 처리
if mafia_num == 0 :
    start_node = 0
else :
    start_node = mafia[0]

# 그래프 탐색으로 특종하지 않아야 할 경우를 반환받는다.
is_not_report = bfs(start_node, users)

# 기자임이 알려지지 않으면서, 특종 할 수 있는 턴 개수의 최댓값 구하기
answer = 0
for i in range(m) :
    turn = turns[i]
    turn_num = len(turn)

    # 이번 턴에서 한 마피아에게 기자임이 알려질 수 있다면, 답이 아니다.
    success = True
    for j in range(turn_num) :
        if is_not_report[turn[j]] :
            success = False
            break

    if success :
        answer += 1

print(answer)
