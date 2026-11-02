#include<iostream>
#include<algorithm>
using namespace std;

int n, m;
int arr[1010][1010];

int main()
{
	int q, Q;
	int i, j;
	int x1, y1, x2, y2, x3, y3, x4, y4;
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
		cin >> x1 >> y1 >> x2 >> y2 >> x3 >> y3 >> x4 >> y4;

		ans = 0;
		for (i = 1; i <= n; i++)
		{
			for (j = 1; j <= m; j++)
			{
				if (x1 <= i && i <= x2 && y1 <= j && j <= y2) continue;
				if (x3 <= i && i <= x4 && y3 <= j && j <= y4) continue;

				ans = max(ans, arr[i][j]);
			}
		}

		cout << ans << '\n';
	}
}
