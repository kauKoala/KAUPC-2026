"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import random
import sys

random.seed(int(sys.argv[1]))

# ---- 여기부터 출제자가 쓴다 ----

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
# 기능 이름은 작업 이름과 같지 않다.
COMMANDS = {"feat", "fix", "hotfix", "deprecate", "issue"}

# 시드마다 작업 구성을 바꾼다. 이름 풀이 좁으면 같은 기능이 계속 갱신되어 힙에 낡은 항목이 쌓인다.
shape = random.choice(["max", "churn", "wide", "issue-heavy", "deprecate-heavy", "small"])

if shape == "max":
    x, pool, weights = 200000, 2000, {"feat": 25, "fix": 15, "hotfix": 25, "deprecate": 10, "issue": 25}
elif shape == "churn":
    x, pool, weights = random.randint(50000, 200000), 8, {"feat": 30, "fix": 5, "hotfix": 40, "deprecate": 5, "issue": 20}
elif shape == "wide":
    x, pool, weights = random.randint(50000, 200000), 5000, {"feat": 45, "fix": 5, "hotfix": 10, "deprecate": 10, "issue": 30}
elif shape == "issue-heavy":
    x, pool, weights = random.randint(20000, 200000), 300, {"feat": 15, "fix": 5, "hotfix": 10, "deprecate": 5, "issue": 65}
elif shape == "deprecate-heavy":
    x, pool, weights = random.randint(20000, 200000), 200, {"feat": 30, "fix": 5, "hotfix": 10, "deprecate": 35, "issue": 20}
else:
    x, pool, weights = random.randint(1, 50), 5, {"feat": 30, "fix": 10, "hotfix": 20, "deprecate": 10, "issue": 30}

names = set()
while len(names) < pool:
    size = random.randint(1, 20)
    candidate = "".join(random.choice(ALPHABET) for _ in range(size))
    if candidate not in COMMANDS:
        names.add(candidate)
names = sorted(names)

commands = list(weights)
chances = [weights[command] for command in commands]

lines = []
for _ in range(x):
    command = random.choices(commands, weights=chances, k=1)[0]
    if command == "feat":
        lines.append("feat " + random.choice(names) + " " + str(random.randint(0, 10000)))
    elif command == "fix":
        lines.append("fix " + str(random.randint(0, 10000)))
    elif command == "hotfix":
        lines.append("hotfix " + random.choice(names) + " " + str(random.randint(0, 10000)))
    elif command == "deprecate":
        lines.append("deprecate " + random.choice(names))
    else:
        lines.append("issue")

# issue는 반드시 하나 이상 있어야 한다.
if "issue" not in lines:
    lines[random.randrange(x)] = "issue"

print(x)
print("\n".join(lines))
