#include <bits/stdc++.h>
using namespace std;

constexpr long long INF = (1LL << 60);

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, q;
    if (!(cin >> n >> m >> q)) return 0;
    vector<vector<long long>> dist(n, vector<long long>(n, INF));
    for (int i = 0; i < n; ++i) dist[i][i] = 0;
    for (int i = 0, a, b; i < m; ++i) {
        long long c;
        cin >> a >> b >> c;
        --a; --b;
        dist[a][b] = min(dist[a][b], c);
        dist[b][a] = min(dist[b][a], c);
    }
    for (int k = 0; k < n; ++k)
        for (int i = 0; i < n; ++i) if (dist[i][k] != INF)
            for (int j = 0; j < n; ++j)
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j]);

    while (q--) {
        int type, a, b;
        cin >> type >> a >> b;
        --a; --b;
        if (type == 1) {
            long long c;
            cin >> c;
            for (int i = 0; i < n; ++i) {
                for (int j = 0; j < n; ++j) {
                    dist[i][j] = min({dist[i][j], dist[i][a] + c + dist[b][j], dist[i][b] + c + dist[a][j]});
                }
            }
        } else {
            cout << (dist[a][b] == INF ? -1 : dist[a][b]) << '\n';
        }
    }
}
