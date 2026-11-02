#include <stdio.h>
#include <stdlib.h>

#define MAXN 300
#define INF 0x3f3f3f3f3f3f3f3fLL

static long long dist[MAXN][MAXN];
static long long to_u[MAXN], to_v[MAXN], from_u[MAXN], from_v[MAXN];

int main(void) {
    int n, m, q;
    if (scanf("%d %d %d", &n, &m, &q) != 3) return 0;

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) dist[i][j] = (i == j) ? 0 : INF;
    }

    for (int e = 0; e < m; ++e) {
        int a, b;
        long long c;
        scanf("%d %d %lld", &a, &b, &c);
        --a; --b;
        if (c < dist[a][b]) {
            dist[a][b] = c;
            dist[b][a] = c;
        }
    }

    for (int k = 0; k < n; ++k) {
        for (int i = 0; i < n; ++i) {
            long long through = dist[i][k];
            if (through == INF) continue;
            for (int j = 0; j < n; ++j) {
                long long candidate = through + dist[k][j];
                if (candidate < dist[i][j]) dist[i][j] = candidate;
            }
        }
    }

    for (int t = 0; t < q; ++t) {
        int type;
        scanf("%d", &type);
        if (type == 1) {
            int u, v;
            long long w;
            scanf("%d %d %lld", &u, &v, &w);
            --u; --v;
            for (int i = 0; i < n; ++i) {
                to_u[i] = dist[i][u];
                to_v[i] = dist[i][v];
                from_u[i] = dist[u][i];
                from_v[i] = dist[v][i];
            }
            for (int i = 0; i < n; ++i) {
                long long via_u = to_u[i] + w;
                long long via_v = to_v[i] + w;
                for (int j = 0; j < n; ++j) {
                    long long candidate = via_u + from_v[j];
                    long long other = via_v + from_u[j];
                    if (other < candidate) candidate = other;
                    if (candidate < dist[i][j]) dist[i][j] = candidate;
                }
            }
        } else {
            int a, b;
            scanf("%d %d", &a, &b);
            long long answer = dist[a - 1][b - 1];
            printf("%lld\n", answer >= INF ? -1LL : answer);
        }
    }
    return 0;
}
