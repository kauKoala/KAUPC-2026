"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import random
import sys

random.seed(int(sys.argv[1]))

# ---- 여기부터 출제자가 쓴다 ----

if sys.argv[1] == "1":
    # 가장 긴 경로가 답이 아닌 경우. 지름만 보는 풀이가 틀린다.
    print("10\n1 2 3\n2 3 3\n3 4 3\n4 5 3\n1 6 3\n6 7 3\n7 8 3\n8 9 3\n1 10 11")
    sys.exit()

n = random.choice([random.randint(2, 30), 200000])
shape = random.choice(["path", "star", "random"])
w_max = random.choice([10, 1000])

edges = []
for i in range(2, n + 1):
    if shape == "path":
        parent = i - 1
    elif shape == "star":
        parent = 1
    else:
        parent = random.randint(1, i - 1)
    edges.append((parent, i, random.randint(1, w_max)))

# 정점 번호를 섞는다.
label = list(range(1, n + 1))
random.shuffle(label)
print(n)
for u, v, w in edges:
    print(label[u - 1], label[v - 1], w)
