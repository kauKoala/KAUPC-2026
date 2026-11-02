import heapq
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    position = 0
    operations = int(data[position])
    position += 1

    usage = {}
    low = []
    output = []

    def add(name: bytes, value: int) -> None:
        usage[name] = value
        heapq.heappush(low, (value, name))

    def lowest():
        while low:
            value, name = low[0]
            if usage.get(name) == value:
                return value, name
            heapq.heappop(low)
        return None


    for _ in range(operations):
        command = data[position]
        position += 1
        if command == b"feat":
            name = data[position]
            amount = int(data[position + 1])
            position += 2
            if name not in usage:
                add(name, amount)
        elif command == b"fix":
            amount = int(data[position])
            position += 1
            found = lowest()
            if found:
                value, name = found
                add(name, value + amount)
        elif command == b"hotfix":
            name = data[position]
            amount = int(data[position + 1])
            position += 2
            if name in usage:
                add(name, usage[name] + amount)
        elif command == b"deprecate":
            name = data[position]
            position += 1
            usage.pop(name, None)
        else:
            found = lowest()
            if found:
                value, name = found
                output.append(name + b" " + str(value).encode())
            else:
                output.append(b"-1")

    if output:
        sys.stdout.buffer.write(b"\n".join(output) + b"\n")


if __name__ == "__main__":
    main()
