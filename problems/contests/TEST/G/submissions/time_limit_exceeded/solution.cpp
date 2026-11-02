#include <iostream>
#include <vector>
#include <cstdlib>

using namespace std;

int main() {
    int N, L, R;
    cin >> N >> L >> R;

    vector<int> v(N);
    for (int i = 0; i < N; i++) {
        cin >> v[i];
    }

    long long ans = 0;
    for (int i = 0; i < N; i++) {
        for (int j = i + 1; j < N; j++) {
            int d = abs(v[i] - v[j]);
            if (L <= d && d <= R) ans++;
        }
    }

    cout << ans;
}
