import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, low, high = data[:3]
    values = sorted(data[3 : 3 + n])
    first_over_high = 0
    first_at_least_low = 0
    answer = 0
    for right, value in enumerate(values):
        while value - values[first_over_high] > high:
            first_over_high += 1
        while first_at_least_low < right and value - values[first_at_least_low] >= low:
            first_at_least_low += 1
        answer += first_at_least_low - first_over_high
    print(answer)


if __name__ == "__main__":
    main()
