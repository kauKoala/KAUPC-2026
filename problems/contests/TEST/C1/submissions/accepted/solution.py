import sys


def main() -> None:
    a, b = (int(x) for x in sys.stdin.read().split())
    print(a * b)


if __name__ == "__main__":
    main()
