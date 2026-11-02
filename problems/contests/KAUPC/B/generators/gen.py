"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import random
import sys

random.seed(int(sys.argv[1]))

# ---- 여기부터 출제자가 쓴다 ----

import itertools
import random

shapes = ["마름모", "타원", "물결"]
shades = ["채움", "테두리", "빗금"]
colors = ["빨강", "보라", "초록"]
counts = ["1개", "2개", "3개"]
attrs = [shapes, shades, colors, counts]

# 카드는 (모양, 음영, 색깔, 개수) 각 0~2. 세 카드가 트리플, 모든 속성에서 합이 3의 배수.
deck = list(itertools.product(range(3), repeat=4))

def third(x, y):
    return tuple((-x[a] - y[a]) % 3 for a in range(4))

def cap_set():
    # 트리플이 하나도 없는 집합을 무작위 탐욕으로 만든다 (보통 16~20장)
    order = deck[:]
    random.shuffle(order)
    cap, banned = [], set()
    for c in order:
        if c in banned:
            continue
        for d in cap:
            banned.add(third(c, d))
        cap.append(c)
    return cap

# 시드마다 카드 구성을 바꾼다.
shape = random.choice(["uniform", "small", "large", "full", "no-triple", "one-extra", "fixed-attr", "aba-trap"])

if shape == "uniform":            # 원래 생성기와 같음: N 무작위, 카드 무작위
    cards = random.sample(deck, random.randint(3, 81))
elif shape == "small":            # N이 작아 트리플 0~수 개 → "No triple" 분기와 경계 검사
    cards = random.sample(deck, random.randint(3, 10))
elif shape == "large":            # 출력이 많아 순서 오류·느린 풀이를 잡는다
    cards = random.sample(deck, random.randint(70, 81))
elif shape == "full":             # 81장 전부, 순서만 섞음 → 트리플 1080개
    cards = deck[:]
    random.shuffle(cards)
elif shape == "no-triple":        # 큰 N에서 "No triple"
    cards = cap_set()
    random.shuffle(cards)
elif shape == "one-extra":        # cap set 뒤에 1장 → 모든 트리플이 마지막 카드를 포함
    cards = cap_set()
    random.shuffle(cards)
    rest = [c for c in deck if c not in cards]
    cards.append(random.choice(rest))
elif shape == "fixed-attr":       # 속성 하나를 고정 → "모두 같음" 속성이 반드시 끼어 있는 트리플
    a, v = random.randrange(4), random.randrange(3)
    pool = [c for c in deck if c[a] == v]
    cards = random.sample(pool, random.randint(3, 27))
else:                             # aba-trap: 값 2를 거의 안 써서 X-Y-X 함정이 많다
    pool = [c for c in deck if sum(1 for x in c if x == 2) <= 1]
    cards = random.sample(pool, random.randint(3, len(pool)))

print(len(cards))
for c in cards:
    print(" ".join(attrs[i][c[i]] for i in range(4)))
