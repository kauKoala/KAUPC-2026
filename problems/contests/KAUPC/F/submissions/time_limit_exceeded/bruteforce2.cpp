#include<iostream>
#include<vector>
#include<algorithm>
using namespace std;

int n, m;
int arr[1010][1010];
vector<pair<int, pair<int, int>>> v;

bool comp(pair<int, pair<int, int>> a, pair<int, pair<int, int>> b)
{
	return a.first > b.first;
}

int main()
{
	int q, Q;
	int i, j;
	int x1, y1, x2, y2;
	int x, y;
	int ans;

	cin >> n >> m;
	for (i = 1; i <= n; i++)
	{
		for (j = 1; j <= m; j++)
		{
			cin >> arr[i][j];

			v.push_back(make_pair(arr[i][j], make_pair(i, j)));
		}
	}

	sort(v.begin(), v.end(), comp);

	cin >> Q;
	for (q = 1; q <= Q; q++)
	{
		cin >> x1 >> y1 >> x2 >> y2;

		ans = 0;
		for (i = 0; i < v.size(); i++)
		{
			x = v[i].second.first;
			y = v[i].second.second;

			if (x1 <= x && x <= x2 && y1 <= y && y <= y2) continue;

			ans = v[i].first;
			break;
		}

		cout << ans << '\n';
	}
}
