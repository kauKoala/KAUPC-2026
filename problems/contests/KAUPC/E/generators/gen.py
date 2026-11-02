"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import random
import sys

random.seed(int(sys.argv[1]))

# ---- 여기부터 출제자가 쓴다 ----

seed = int(sys.argv[1])
MAX_N = 300000
MAX_V = 10**9

# 시드 1~9는 정해진 경계 케이스, 그 외는 무작위.
if seed == 1:    # 최소 N, 짝 1개
    n, low, high, a = 2, 0, MAX_V, [0, MAX_V]
elif seed == 2:  # 최소 N, 짝 없음
    n, low, high, a = 2, 3, 5, [10, 12]
elif seed == 3:  # 차이가 정확히 L = R
    n, low, high, a = 6, 3, 3, [1, 4, 7, 10, 2, 5]
elif seed == 4:  # L = 0, 같은 값이 여럿
    n, low, high, a = 8, 0, 1, [5, 5, 6, 6, 6, 9, 9, 10]
elif seed == 5:  # 모든 쌍이 조건을 만족해 답이 int 범위를 넘는다
    n, low, high = MAX_N, 0, MAX_V
    a = [random.randint(0, MAX_V) for _ in range(n)]
elif seed == 6:  # 모두 같은 값, L = 0
    n, low, high, a = MAX_N, 0, 0, [MAX_V] * MAX_N
elif seed == 7:  # 모두 같은 값, L >= 1이라 답 0
    n, low, high, a = MAX_N, 1, MAX_V, [7] * MAX_N
elif seed == 8:  # 등차수열이라 차이가 정확히 L, R인 쌍이 많다
    n, low, high = MAX_N, 30, 60
    a = [3 * i for i in range(n)][::-1]
elif seed == 9:  # 값의 범위가 좁아 중복이 많다
    n, low, high = MAX_N, 3, 17
    a = [random.randint(0, 1000) for _ in range(n)]
else:
    n = random.choice([random.randint(2, 50), random.randint(1000, 20000), MAX_N])
    value_max = random.choice([10, 1000, 10**6, MAX_V])
    low = random.randint(0, value_max)
    high = random.randint(low, value_max)
    a = [random.randint(0, value_max) for _ in range(n)]

print(n, low, high)
print(" ".join(map(str, a)))
