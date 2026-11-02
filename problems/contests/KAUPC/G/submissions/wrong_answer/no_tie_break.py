import heapq
import sys


def main() -> None:
    # 같은 사용 지수일 때 이름 사전순 대신 삽입 순서를 쓰는 오답 풀이.
    data = sys.stdin.buffer.read().split()
    position = 0
    operations = int(data[position])
    position += 1

    usage = {}
    heap = []
    output = []
    counter = 0

    def discard_stale() -> None:
        while heap:
            value, _, name = heap[0]
            if usage.get(name) == value:
                return
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
                counter += 1
                heapq.heappush(heap, (amount, counter, name))
        elif command == b"fix":
            amount = int(data[position])
            position += 1
            discard_stale()
            if not heap:
                continue
            value, _, name = heapq.heappop(heap)
            usage[name] = value + amount
            counter += 1
            heapq.heappush(heap, (value + amount, counter, name))
        elif command == b"hotfix":
            name = data[position]
            amount = int(data[position + 1])
            position += 2
            if name in usage:
                usage[name] += amount
                counter += 1
                heapq.heappush(heap, (usage[name], counter, name))
        elif command == b"deprecate":
            name = data[position]
            position += 1
            usage.pop(name, None)
        else:
            discard_stale()
            if not heap:
                output.append(b"-1")
            else:
                value, _, name = heap[0]
                output.append(name + b" " + str(value).encode())

    if output:
        sys.stdout.buffer.write(b"\n".join(output) + b"\n")


if __name__ == "__main__":
    main()
