#include<iostream>
#include<algorithm>
using namespace std;

int n, m;
int arr[1010][1010];

int main()
{
	int q, Q;
	int i, j;
	int x1, y1, x2, y2;
	int ans;

	cin >> n >> m;
	for (i = 1; i <= n; i++)
	{
		for (j = 1; j <= m; j++)
		{
			cin >> arr[i][j];
		}
	}
	cin >> Q;
	for (q = 1; q <= Q; q++)
	{
		cin >> x1 >> y1 >> x2 >> y2;

		ans = 0;
		for (i = 1; i < x1; i++)
		{
			for (j = 1; j <= m; j++)
			{
				ans = max(ans, arr[i][j]);
			}
		}
		for (i = x2 + 1; i <= n; i++)
		{
			for (j = 1; j <= m; j++)
			{
				ans = max(ans, arr[i][j]);
			}
		}
		for (j = 1; j < y1; j++)
		{
			for (i = 1; i <= n; i++)
			{
				ans = max(ans, arr[i][j]);
			}
		}
		for (j = y2 + 1; j <= m; j++)
		{
			for (i = 1; i <= n; i++)
			{
				ans = max(ans, arr[i][j]);
			}
		}

		cout << ans << '\n';
	}
}
