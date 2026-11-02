import sys


def solve() -> None:
    input = sys.stdin.buffer.readline
    n, m, q = map(int, input().split())
    inf = 10**30
    dist = [[inf] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0

    for _ in range(m):
        a, b, c = map(int, input().split())
        a -= 1
        b -= 1
        if c < dist[a][b]:
            dist[a][b] = c
            dist[b][a] = c

    for k in range(n):
        dist_k = dist[k]
        for i in range(n):
            through_k = dist[i][k]
            if through_k == inf:
                continue
            dist_i = dist[i]
            for j in range(n):
                candidate = through_k + dist_k[j]
                if candidate < dist_i[j]:
                    dist_i[j] = candidate

    output = []
    for _ in range(q):
        query = list(map(int, input().split()))
        if query[0] == 1:
            _, u, v, w = query
            u -= 1
            v -= 1
            to_u = [dist[i][u] for i in range(n)]
            to_v = [dist[i][v] for i in range(n)]
            from_u = dist[u][:]
            from_v = dist[v][:]
            for i in range(n):
                via_u = to_u[i] + w
                via_v = to_v[i] + w
                dist_i = dist[i]
                for j in range(n):
                    candidate = min(via_u + from_v[j], via_v + from_u[j])
                    if candidate < dist_i[j]:
                        dist_i[j] = candidate
        else:
            _, a, b = query
            answer = dist[a - 1][b - 1]
            output.append(str(answer if answer < inf else -1))

    sys.stdout.write("\n".join(output))
    if output:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()
