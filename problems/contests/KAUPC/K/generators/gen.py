"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import random
import sys

random.seed(int(sys.argv[1]))

# ---- 여기부터 출제자가 쓴다 ----

import random

N = random.randint(800, 1000)
M = random.randint(800, 1000)
Q = random.randint(90000, 100000)

arr = [[] for i in range(N)]
sx = random.randint(5, 100)
ex = random.randint(N - 100, N - 5)
sy = random.randint(5, 100)
ey = random.randint(M - 100, M - 5)

nums = list(range(1, 500001)) + list(range(1, 500001))
for i in range(N):
    for j in range(M):
        if i < sx or i > ex or j < sy or j > ey:
            idx = random.randint(0, len(nums) - 1)
            arr[i].append(nums[idx])
            nums[idx] = nums[-1]
            nums.pop()
        else:
            arr[i].append(random.randint(500001, 1000000))

query = []
while len(query) < Q:
    x1 = random.randint(1, sx)
    y1 = random.randint(1, sy)
    x2 = random.randint(ex, N)
    y2 = random.randint(ey, M)

    # 두번째 사각형을 위에 둘지, x 상관 없이 둘지, 아래에 둘지
    dx = random.randint(1, 3)
    if dx == 1:
        # 위에 두려는데 x1이 1이면 x1을 내림.
        if x1 == 1:
            x1 = random.randint(2, sx)

        x3 = random.randint(1, x1 - 1)
        x4 = random.randint(x3, x1 - 1)
    elif dx == 2:
        x3 = random.randint(1, N)
        x4 = random.randint(x3, N)
    else:
        # 아래에 두려는데 x2가 N이면 x2를 올림
        if x2 == N:
            x2 = random.randint(ex, N - 1)

        x3 = random.randint(x2 + 1, N)
        x4 = random.randint(x3, N)

    # 두번째 사각형을 왼쪽에 둘지, y 상관 없이 둘지, 오른쪽에 둘지.
    # dx가 2라면 dy는 1이나 3으로
    if dx == 2:
        dy = [1, 3][random.randint(0, 1)]
    else:
        dy = random.randint(1, 3)

    if dy == 1:
        if y1 == 1:
            y1 = random.randint(2, sy)

        y3 = random.randint(1, y1 - 1)
        y4 = random.randint(y3, y1 - 1)
    elif dy == 2:
        y3 = random.randint(1, M)
        y4 = random.randint(y3, M)
    else:
        # 아래에 두려는데 x2가 N이면 x2를 올림
        if y2 == M:
            y2 = random.randint(ey, M - 1)

        y3 = random.randint(y2 + 1, M)
        y4 = random.randint(y3, M)

    query.append([x1, y1, x2, y2, x3, y3, x4, y4])

print(N, M)
for i in range(N):
    print(*arr[i])
print(Q)
for i in range(Q):
    print(*query[i])
