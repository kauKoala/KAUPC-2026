import sys
input = sys.stdin.readline

n, t = map(int, input().split())
d = [int(input().split()[1]) for _ in range(n)]
d.sort()

cnt = total = 0
for x in d:
    if total + x > t:
        break
    total += x
    cnt += 1
print(cnt, total)
