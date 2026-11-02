#include<iostream>
#include<algorithm>
using namespace std;

int n, m;
int arr[1010][1010];
int l[1010], r[1010], u[1010], d[1010];

int main()
{
	int q, Q;
	int i, j;
	int x1, y1, x2, y2;
	int ans;

	cin.tie(NULL);
	ios::sync_with_stdio(false);

	cin >> n >> m;
	for (i = 1; i <= n; i++)
	{
		for (j = 1; j <= m; j++)
		{
			cin >> arr[i][j];
		}
	}

	for (j = 1; j <= m; j++)
	{
		l[j] = l[j - 1];
		for (i = 1; i <= n; i++)
		{
			l[j] = max(l[j], arr[i][j]);
		}
	}
	for (j = m; j >= 1; j--)
	{
		r[j] = r[j + 1];
		for (i = 1; i <= n; i++)
		{
			r[j] = max(r[j], arr[i][j]);
		}
	}
	for (i = 1; i <= n; i++)
	{
		u[i] = u[i - 1];
		for (j = 1; j <= m; j++)
		{
			u[i] = max(u[i], arr[i][j]);
		}
	}
	for (i = n; i >= 1; i--)
	{
		d[i] = d[i + 1];
		for (j = 1; j <= m; j++)
		{
			d[i] = max(d[i], arr[i][j]);
		}
	}

	cin >> Q;
	for (q = 1; q <= Q; q++)
	{
		cin >> x1 >> y1 >> x2 >> y2;

		ans = max(max(l[y1 - 1], r[y2 + 1]), max(u[x1 - 1], d[x2 + 1]));

		cout << ans << '\n';
	}
}
