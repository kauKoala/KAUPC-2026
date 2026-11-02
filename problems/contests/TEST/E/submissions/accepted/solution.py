import sys


def main() -> None:
    n = int(sys.stdin.readline())
    sys.stdout.write("".join("*" * i + "\n" for i in range(1, n + 1)))


if __name__ == "__main__":
    main()
