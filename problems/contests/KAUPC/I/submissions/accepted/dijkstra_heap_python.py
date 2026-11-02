"""Per-query O((N+M) log N) Dijkstra reference."""

import heapq
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    at = 0
    n, m, q = map(int, data[:3])
    at = 3
    graph = [[] for _ in range(n)]
    for _ in range(m):
        a, b, w = int(data[at]) - 1, int(data[at + 1]) - 1, int(data[at + 2])
        at += 3
        graph[a].append((b, w))
        graph[b].append((a, w))
    out = []
    for _ in range(q):
        kind = int(data[at]); at += 1
        a, b = int(data[at]) - 1, int(data[at + 1]) - 1
        at += 2
        if kind == 1:
            w = int(data[at]); at += 1
            graph[a].append((b, w))
            graph[b].append((a, w))
            continue
        inf = 10**30
        dist = [inf] * n
        dist[a] = 0
        heap = [(0, a)]
        while heap:
            value, node = heapq.heappop(heap)
            if value != dist[node]:
                continue
            if node == b:
                break
            for vertex, weight in graph[node]:
                candidate = value + weight
                if candidate < dist[vertex]:
                    dist[vertex] = candidate
                    heapq.heappush(heap, (candidate, vertex))
        out.append(str(dist[b] if dist[b] < inf else -1))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
