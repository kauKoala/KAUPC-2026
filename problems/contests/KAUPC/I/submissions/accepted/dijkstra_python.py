"""2번 쿼리마다 다익스트라를 새로 도는 풀이. 서버(PyPy)에서 시간 제한 안에 통과한다."""

import heapq
import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    position = 0
    n = int(data[position])
    m = int(data[position + 1])
    q = int(data[position + 2])
    position += 3

    graph = [[] for _ in range(n)]
    for _ in range(m):
        a = int(data[position]) - 1
        b = int(data[position + 1]) - 1
        c = int(data[position + 2])
        position += 3
        graph[a].append((b, c))
        graph[b].append((a, c))

    output = []
    for _ in range(q):
        kind = int(data[position])
        position += 1
        if kind == 1:
            u = int(data[position]) - 1
            v = int(data[position + 1]) - 1
            w = int(data[position + 2])
            position += 3
            graph[u].append((v, w))
            graph[v].append((u, w))
        else:
            start = int(data[position]) - 1
            goal = int(data[position + 1]) - 1
            position += 2
            best = [float("inf")] * n
            best[start] = 0
            queue = [(0, start)]
            while queue:
                current, node = heapq.heappop(queue)
                if current > best[node]:
                    continue
                for nxt, weight in graph[node]:
                    candidate = current + weight
                    if candidate < best[nxt]:
                        best[nxt] = candidate
                        heapq.heappush(queue, (candidate, nxt))
            answer = best[goal]
            output.append(str(answer if answer != float("inf") else -1))

    sys.stdout.write("\n".join(output))
    if output:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()
