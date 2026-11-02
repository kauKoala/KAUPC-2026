"""0개부터 찍어서 첫 줄이 빈 줄이 되는 오답."""
import sys

n = int(sys.stdin.readline())
for i in range(n):
    print("*" * i)
