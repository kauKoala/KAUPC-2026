import sys


def render(heights: list[int]) -> str:
    canvas = [["."] * 10 for _ in range(5)]
    for line in range(3):
        for column, letter in enumerate("KAUPC"):
            row = line + 1 - heights[column]
            canvas[row][column * 2] = letter
            canvas[row][column * 2 + 1] = letter
    return "\n".join("".join(row) for row in canvas) + "\n"


def main() -> None:
    heights = list(map(int, sys.stdin.readline().split()))
    sys.stdout.write(render(heights))


if __name__ == "__main__":
    main()
