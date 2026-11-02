"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import random
import sys

random.seed(int(sys.argv[1]))

# ---- 여기부터 출제자가 쓴다 ----

import random
import sys

MAX_N = 100
MAX_M = 50


def danger_flags(n, mafias, turns):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(1, len(mafias)):
        union(mafias[0], mafias[i])
    for t in turns:
        for i in range(1, len(t)):
            union(t[0], t[i])
    if not mafias:
        return [False] * len(turns)
    danger = find(mafias[0])
    return [any(find(x) == danger for x in t) for t in turns]


def valid(n, mafias, turns):
    if not (2 <= n <= MAX_N) or not (1 <= len(turns) <= MAX_M):
        return False
    if not (0 <= len(mafias) < n):
        return False
    if any(not t or len(set(t)) != len(t) or any(x < 1 or x > n for x in t) for t in turns):
        return False
    return True


def build():
    shape = random.choice([
        "uniform", "small", "chain", "two_hop", "no_mafia", "mafia_isolated",
        "hub", "clusters", "max_size", "dense", "order_trap",
    ])

    if shape == "small":
        n = random.randint(2, 8)
        m = random.randint(1, 6)
        turns = [random.sample(range(1, n + 1), random.randint(1, n)) for _ in range(m)]
        mafias = random.sample(range(1, n + 1), random.randint(0, min(2, n - 1)))

    elif shape == "chain":
        n = random.randint(10, MAX_N)
        m = min(MAX_M, n - 1)
        turns = [[i, i + 1] for i in range(1, m + 1)]
        if random.random() < 0.5:
            turns.reverse()
        mafias = [random.choice([1, m + 1])]

    elif shape == "two_hop":
        n = random.randint(8, 40)
        depth = random.randint(2, min(6, n // 2))
        turns = [[i, i + 1] for i in range(1, depth + 1)]
        nxt = depth + 2
        while nxt + 1 <= n and len(turns) < MAX_M:
            turns.append([nxt, nxt + 1])
            nxt += 2
        mafias = [1]

    elif shape == "no_mafia":
        n = random.randint(2, MAX_N)
        m = random.randint(1, MAX_M)
        turns, seen = [], set()
        for _ in range(m):
            for _try in range(50):
                t = tuple(sorted(random.sample(range(1, n + 1), random.randint(1, min(n, 10)))))
                if t not in seen:
                    break
            seen.add(t)
            turns.append(list(t))
        mafias = []

    elif shape == "mafia_isolated":
        n = random.randint(10, MAX_N)
        m = random.randint(1, MAX_M)
        turns, seen = [], set()
        for _ in range(m):
            for _try in range(50):
                t = tuple(sorted(random.sample(range(2, n + 1), random.randint(1, min(n - 1, 10)))))
                if t not in seen:
                    break
            seen.add(t)
            turns.append(list(t))
        mafias = [1]

    elif shape == "hub":
        n = random.randint(20, MAX_N)
        m = random.randint(2, MAX_M)
        turns = []
        for _ in range(m):
            others = random.sample(range(2, n + 1), random.randint(1, min(n - 1, 10)))
            turns.append([1] + others)
        mafias = [random.randint(1, n)]

    elif shape == "clusters":
        n = random.randint(20, MAX_N)
        groups = random.randint(2, 5)
        m = random.randint(groups, MAX_M)
        bounds = [1 + (n * g) // groups for g in range(groups + 1)]
        turns = []
        for t in range(m):
            g = t % groups
            lo, hi = bounds[g], min(bounds[g + 1] - 1, n)
            k = min(random.randint(1, 8), hi - lo + 1)
            turns.append(random.sample(range(lo, hi + 1), k))
        appear = sorted({x for t in turns for x in t})
        mafias = random.sample(appear, min(random.randint(1, 3), len(appear), n - 1))

    elif shape == "max_size":
        n = MAX_N
        m = MAX_M
        turns = [random.sample(range(1, n + 1), random.randint(5, 30)) for _ in range(m)]
        mafias = [turns[0][0]] if random.random() < 0.7 else []

    elif shape == "dense":
        n = random.randint(50, MAX_N)
        m = random.randint(10, MAX_M)
        turns = []
        for _ in range(m):
            t = list(range(1, n + 1))
            random.shuffle(t)
            turns.append(t)
        mafias = [random.randint(1, n)]

    elif shape == "order_trap":
        n = random.randint(10, 60)
        mafias = [1]
        turns = [[1, 2], [2, 3]]
        turns += [[4, 5], [1, 4]]
        nxt = 6
        while nxt + 1 <= n and len(turns) < MAX_M:
            turns.append([nxt, nxt + 1])
            nxt += 2
        random.shuffle(turns)

    else:  # uniform
        n = random.randint(2, MAX_N)
        m = random.randint(1, MAX_M)
        max_k = min(n, 12)
        turns = [random.sample(range(1, n + 1), random.randint(1, max_k)) for _ in range(m)]
        appear = sorted({x for t in turns for x in t})
        mafias = random.sample(appear, min(random.randint(0, 3), len(appear), n - 1))

    return n, mafias, turns


if __name__ == "__main__":
    if len(sys.argv) > 1:
        random.seed(int(sys.argv[1]))
    for _ in range(300):
        n, mafias, turns = build()
        if valid(n, mafias, turns):
            break
    else:
        n, mafias, turns = 2, [1], [[1, 2]]

    print(n, len(turns))
    print(len(mafias))
    print(" ".join(map(str, mafias)) if mafias else "0")
    for t in turns:
        print(len(t))
        print(" ".join(map(str, t)))
