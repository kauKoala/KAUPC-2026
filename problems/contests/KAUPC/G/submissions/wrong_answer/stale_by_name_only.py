"""낡은 힙 항목을 이름 존재 여부로만 거르는 오답 풀이. 값이 바뀐 옛 항목이 살아남는다."""

import heapq
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    position = 0
    operations = int(data[position])
    position += 1

    usage = {}
    heap = []
    output = []

    def discard_stale() -> None:
        while heap and heap[0][1] not in usage:
            heapq.heappop(heap)

    for _ in range(operations):
        command = data[position]
        position += 1
        if command == b"feat":
            name = data[position]
            amount = int(data[position + 1])
            position += 2
            if name not in usage:
                usage[name] = amount
                heapq.heappush(heap, (amount, name))
        elif command == b"fix":
            amount = int(data[position])
            position += 1
            discard_stale()
            if not heap:
                continue
            value, name = heapq.heappop(heap)
            usage[name] = value + amount
            heapq.heappush(heap, (value + amount, name))
        elif command == b"hotfix":
            name = data[position]
            amount = int(data[position + 1])
            position += 2
            if name in usage:
                usage[name] += amount
                heapq.heappush(heap, (usage[name], name))
        elif command == b"deprecate":
            usage.pop(data[position], None)
            position += 1
        else:
            discard_stale()
            if not heap:
                output.append(b"-1")
            else:
                value, name = heap[0]
                output.append(name + b" " + str(value).encode())

    if output:
        sys.stdout.buffer.write(b"\n".join(output) + b"\n")


if __name__ == "__main__":
    main()
