"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import random
import sys

random.seed(int(sys.argv[1]))
smoke = len(sys.argv) == 3 and sys.argv[2] == "--smoke"

# ---- 여기부터 출제자가 쓴다 ----

import random

N = random.randint(8, 10) if smoke else random.randint(800, 1000)
M = random.randint(8, 10) if smoke else random.randint(800, 1000)
arr = [[random.randint(1, 1000000) for i in range(M)] for i in range(N)]
Q = random.randint(10, 20) if smoke else random.randint(90000, 100000)

v = []
for i in range(N):
    for j in range(M):
        v.append([arr[i][j], i + 1, j + 1])

v.sort(key=lambda x:-x[0])

mnx = [1 << 30] * (N * M + 1)
mxx = [0] * (N * M + 1)
mny = [1 << 30] * (N * M + 1)
mxy = [0] * (N * M + 1)
for i in range(len(v)):
    mnx[i + 1] = min(mnx[i], v[i][1])
    mxx[i + 1] = max(mxx[i], v[i][1])
    mny[i + 1] = min(mny[i], v[i][2])
    mxy[i + 1] = max(mxy[i], v[i][2])

mx_idx = 0
for i in range(1, len(v) + 1):
    if mnx[i] != 1 or mxx[i] != N or mny[i] != 1 or mxy[i] != M:
        mx_idx = i

query = []
for i in range(Q):
    idx = random.randint(1, mx_idx)

    query.append([mnx[idx], mny[idx], mxx[idx], mxy[idx]])

print(N, M)
for i in range(N):
    print(*arr[i])
print(Q)
for i in range(Q):
    print(*query[i])
