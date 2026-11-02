#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    int N, L, R;
    cin >> N >> L >> R;

    vector<int> v(N);
    for (int i = 0; i < N; i++) {
        cin >> v[i];
    }

    sort(v.begin(), v.end());

    long long ans = 0;
    int a = 0, b = 0;
    for (int i = 0; i < N; i++) {
        while (v[i] - v[a] > R) a++;
        while (b < i && v[i] - v[b] >= L) b++;
        ans += b - a;
    }

    cout << ans;
}
