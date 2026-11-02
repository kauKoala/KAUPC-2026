"""시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
"""

import sys


def all_heights() -> list[tuple[int, ...]]:
    cases: list[tuple[int, ...]] = []

    def visit(prefix: tuple[int, ...]) -> None:
        if len(prefix) == 5:
            cases.append(prefix)
            return
        for next_height in (-1, 0, 1):
            if abs(prefix[-1] - next_height) <= 1:
                visit(prefix + (next_height,))

    visit((0,))
    return cases


if __name__ == "__main__":
    print(*all_heights()[int(sys.argv[1]) % len(all_heights())])
