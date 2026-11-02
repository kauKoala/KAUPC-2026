"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import random
import sys

random.seed(int(sys.argv[1]))

# ---- 여기부터 출제자가 쓴다 ----

# random은 시스템이 시드로 고정해 준다. 한 번 실행할 때 입력 하나만 출력한다.
shape = random.choice(["sparse", "dense", "path", "two_blocks", "parallel"])
n = random.randint(180, 300)
q = random.randint(700, 1000)
updates = random.randint(0, min(500, q))

if shape == "sparse":
    m = random.randint(n - 1, 1500)
elif shape == "dense":
    m = random.randint(3000, 5000)
elif shape == "path":
    m = n - 1
elif shape == "two_blocks":
    m = random.randint(n, 3000)
else:
    n = random.randint(2, 40)
    m = random.randint(5000, 50000)

lines = [f"{n} {m} {q}"]
if shape == "path":
    for vertex in range(1, n):
        lines.append(f"{vertex} {vertex + 1} {random.randint(1, 100000)}")
elif shape == "two_blocks":
    middle = n // 2
    for _ in range(m):
        if random.randrange(2):
            a, b = random.randint(1, middle), random.randint(1, middle)
        else:
            a, b = random.randint(middle + 1, n), random.randint(middle + 1, n)
        lines.append(f"{a} {b} {random.randint(1, 100000)}")
else:
    for _ in range(m):
        lines.append(f"{random.randint(1, n)} {random.randint(1, n)} {random.randint(1, 100000)}")

update_positions = set(random.sample(range(q), updates))
for index in range(q):
    if index in update_positions:
        lines.append(f"1 {random.randint(1, n)} {random.randint(1, n)} {random.randint(1, 100000)}")
    else:
        lines.append(f"2 {random.randint(1, n)} {random.randint(1, n)}")

print("\n".join(lines))
