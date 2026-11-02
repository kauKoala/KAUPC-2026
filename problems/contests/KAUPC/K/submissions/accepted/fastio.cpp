#include<iostream>
#include<algorithm>
using namespace std;

int n, m;
int arr[1010][1010];
int ul[1010][1010], ur[1010][1010], dl[1010][1010], dr[1010][1010];
int r[1010], c[1010];
int row[1010][1010], col[1010][1010];

void init()
{
	int i, j;

	for (i = 1; i <= n; i++)
	{
		for (j = 1; j <= m; j++)
		{
			ul[i][j] = max(max(ul[i - 1][j], ul[i][j - 1]), arr[i][j]);
		}

		for (j = m; j >= 1; j--)
		{
			ur[i][j] = max(max(ur[i - 1][j], ur[i][j + 1]), arr[i][j]);
		}
	}

	for (i = n; i >= 1; i--)
	{
		for (j = 1; j <= m; j++)
		{
			dl[i][j] = max(max(dl[i + 1][j], dl[i][j - 1]), arr[i][j]);
		}

		for (j = m; j >= 1; j--)
		{
			dr[i][j] = max(max(dr[i + 1][j], dr[i][j + 1]), arr[i][j]);
		}
	}

	for (i = 1; i <= n; i++)
	{
		for (j = 1; j <= m; j++)
		{
			r[i] = max(r[i], arr[i][j]);
			c[j] = max(c[j], arr[i][j]);
		}
	}

	for (i = 1; i <= n; i++)
	{
		for (j = i; j <= n; j++)
		{
			row[i][j] = max(row[i][j - 1], r[j]);
		}
	}

	for (i = 1; i <= m; i++)
	{
		for (j = i; j <= m; j++)
		{
			col[i][j] = max(col[i][j - 1], c[j]);
		}
	}
}

int main()
{
	int q, Q;
	int i, j;
	int x1, y1, x2, y2, x3, y3, x4, y4;
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

	init();

	cin >> Q;
	for (q = 1; q <= Q; q++)
	{
		cin >> x1 >> y1 >> x2 >> y2 >> x3 >> y3 >> x4 >> y4;

		if (y1 > y4 || x1 > x4)
		{
			swap(x1, x3);
			swap(y1, y3);
			swap(x2, x4);
			swap(y2, y4);
		}

		if (y2 < y3)
		{
			// 두 사각형 사이
			ans = col[y2 + 1][y3 - 1];

			// 왼쪽 사각형의 위, 왼쪽, 아래
			ans = max(ans, ul[x1 - 1][y2]);
			ans = max(ans, col[1][y1 - 1]);
			ans = max(ans, dl[x2 + 1][y2]);

			// 오른쪽 사각형의 위, 오른쪽, 아래
			ans = max(ans, ur[x3 - 1][y3]);
			ans = max(ans, col[y4 + 1][m]);
			ans = max(ans, dr[x4 + 1][y3]);
		}
		else if (x2 < x3)
		{
			// 두 사각형 사이
			ans = row[x2 + 1][x3 - 1];

			// 위 사각형의 왼쪽, 위, 오른쪽
			ans = max(ans, ul[x2][y1 - 1]);
			ans = max(ans, row[1][x1 - 1]);
			ans = max(ans, ur[x2][y2 + 1]);

			// 아래 사각형의 왼쪽, 아래, 오른쪽
			ans = max(ans, dl[x3][y3 - 1]);
			ans = max(ans, row[x4 + 1][n]);
			ans = max(ans, dr[x3][y4 + 1]);
		}
		else
		{
			ans = -1;
		}

		cout << ans << '\n';
	}
}
