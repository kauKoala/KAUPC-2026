import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    values = list(map(int, data[1:1 + n]))
    print(max(values) - min(values))


if __name__ == "__main__":
    main()
