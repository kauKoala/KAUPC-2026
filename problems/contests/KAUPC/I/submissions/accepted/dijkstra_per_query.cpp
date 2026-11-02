#include<iostream>
#include<vector>
#include<queue>
#include<cstring>
using namespace std;

int n, m;
vector<pair<int, int>> v[310];
int dist[310];

int get_dist(int s, int e)
{
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;
    int i;
    int cur, d;
    int nxt, nd;

    memset(dist, 110, sizeof(dist));

    pq.push(make_pair(0, s));
    dist[s] = 0;
    while(!pq.empty())
    {
        cur = pq.top().second;
        d = pq.top().first;
        pq.pop();

        if(cur == e) return d;

        if(dist[cur] != d) continue;

        for(i = 0; i < v[cur].size(); i++)
        {
            nxt = v[cur][i].first;
            nd = d + v[cur][i].second;

            if(dist[nxt] <= nd) continue;

            pq.push(make_pair(nd, nxt));
            dist[nxt] = nd;
        }
    }

    return -1;
}

int main()
{
    int q;
    int i;
    int a, b, c, d;

    cin.tie(NULL);
    ios::sync_with_stdio(false);

    cin >> n >> m >> q;
    for(i = 0; i < m; i++)
    {
        cin >> a >> b >> c;

        v[a].push_back(make_pair(b, c));
        v[b].push_back(make_pair(a, c));
    }

    while(q--)
    {
        cin >> a;

        if(a == 1)
        {
            cin >> b >> c >> d;

            v[b].push_back(make_pair(c, d));
            v[c].push_back(make_pair(b, d));
        }
        else
        {
            cin >> b >> c;

            cout << get_dist(b, c) << '\n';
        }
    }
}
