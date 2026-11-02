#include <iostream>
#include <vector>
#include <queue>
#include <algorithm>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N;
    cin >> N;

    vector<vector<pair<int, int>>> adj(N + 1);
    for (int i = 0; i < N - 1; i++) {
        int u, v, w;
        cin >> u >> v >> w;
        adj[u].push_back({v, w});
        adj[v].push_back({u, w});
    }

    // 1번에서 BFS. 꺼낸 순서를 order에 적고, 각 정점의 부모를 기억한다.
    vector<int> order;
    vector<int> parent(N + 1, 0);
    vector<bool> visited(N + 1, false);
    queue<int> q;
    q.push(1);
    visited[1] = true;
    while (!q.empty()) {
        int v = q.front();
        q.pop();
        order.push_back(v);
        for (auto [c, w] : adj[v]) {
            if (visited[c]) continue;
            visited[c] = true;
            parent[c] = v;
            q.push(c);
        }
    }

    // order를 거꾸로 보면 자식이 부모보다 항상 먼저 나온다.
    vector<int> d0(N + 1, 0), d1(N + 1, 0);
    int ans = 0;
    for (int k = N - 1; k >= 0; k--) {
        int v = order[k];
        int best0 = 0, best1 = 0;
        for (auto [c, w] : adj[v]) {
            if (c == parent[v]) continue;
            int x0 = d0[c] + w;
            int x1 = max(d1[c] + w, d0[c] + 2 * w);
            ans = max({ans, x1 + best0, x0 + best1});
            best0 = max(best0, x0);
            best1 = max(best1, x1);
        }
        d0[v] = best0;
        d1[v] = best1;
    }

    cout << ans;
}
