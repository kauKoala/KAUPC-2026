import random
import sys

# 시드 하나만 받는다. 같은 시드면 항상 같은 데이터가 나온다.
seed = int(sys.argv[1])
random.seed(seed)

n = random.choice([2, 10, 1000, 200000])
bound = 10 ** 9

print(n)
print(" ".join(str(random.randint(-bound, bound)) for _ in range(n)))
