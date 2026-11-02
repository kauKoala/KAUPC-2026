"""매 조회마다 전체 기능을 정렬하는 비효율 풀이. 정답은 맞지만 시간 초과가 나야 한다."""

import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    position = 0
    operations = int(data[position])
    position += 1

    usage = {}
    output = []

    def lowest():
        if not usage:
            return None
        ordered = sorted(usage.items(), key=lambda item: (item[1], item[0]))
        return ordered[0]

    for _ in range(operations):
        command = data[position]
        position += 1
        if command == b"feat":
            name = data[position]
            amount = int(data[position + 1])
            position += 2
            if name not in usage:
                usage[name] = amount
        elif command == b"fix":
            amount = int(data[position])
            position += 1
            target = lowest()
            if target is not None:
                usage[target[0]] = target[1] + amount
        elif command == b"hotfix":
            name = data[position]
            amount = int(data[position + 1])
            position += 2
            if name in usage:
                usage[name] += amount
        elif command == b"deprecate":
            usage.pop(data[position], None)
            position += 1
        else:
            target = lowest()
            if target is None:
                output.append(b"-1")
            else:
                output.append(target[0] + b" " + str(target[1]).encode())

    if output:
        sys.stdout.buffer.write(b"\n".join(output) + b"\n")


if __name__ == "__main__":
    main()
