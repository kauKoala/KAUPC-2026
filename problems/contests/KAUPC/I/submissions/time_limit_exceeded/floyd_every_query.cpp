// 2번 쿼리가 올 때마다 플로이드-워셜을 처음부터 다시 돈다. 2번 쿼리 1,000개면 약 2.7e10번 연산이라 시간 초과가 나야 한다.
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, q;
    cin >> n >> m >> q;
    const long long INF = 1LL << 60;
    vector<vector<long long>> w(n, vector<long long>(n, INF));
    for (int i = 0; i < n; ++i) w[i][i] = 0;
    for (int i = 0; i < m; ++i) {
        int a, b;
        long long c;
        cin >> a >> b >> c;
        --a; --b;
        w[a][b] = min(w[a][b], c);
        w[b][a] = min(w[b][a], c);
    }
    while (q--) {
        int type, a, b;
        cin >> type >> a >> b;
        --a; --b;
        if (type == 1) {
            long long c;
            cin >> c;
            w[a][b] = min(w[a][b], c);
            w[b][a] = min(w[b][a], c);
        } else {
            vector<vector<long long>> d = w;
            for (int k = 0; k < n; ++k)
                for (int i = 0; i < n; ++i)
                    for (int j = 0; j < n; ++j)
                        d[i][j] = min(d[i][j], d[i][k] + d[k][j]);
            cout << (d[a][b] >= INF ? -1 : d[a][b]) << '\n';
        }
    }
}
