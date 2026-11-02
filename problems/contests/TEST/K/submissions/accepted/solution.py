import sys
input = sys.stdin.readline

n, t1, t2 = map(int, input().split())
d = sorted(int(input().split()[-1]) for _ in range(n))

best_cnt, best_time = 0, 0

for mask in range(1 << n):
    s1 = cnt = 0
    for i in range(n):
        if mask >> i & 1:
            s1 += d[i]
            cnt += 1
    if s1 > t1:
        continue
    # 남은 주문을 짧은 순으로 2번 기사에게
    s2 = 0
    for i in range(n):
        if not (mask >> i & 1):
            if s2 + d[i] > t2:
                break
            s2 += d[i]
            cnt += 1
    total = s1 + s2
    if cnt > best_cnt or (cnt == best_cnt and total < best_time):
        best_cnt, best_time = cnt, total

print(best_cnt, best_time)
