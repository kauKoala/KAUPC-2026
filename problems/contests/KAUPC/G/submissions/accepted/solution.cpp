#include <bits/stdc++.h>
using namespace std;

struct Entry { long long value; string name; };
struct Low { bool operator()(const Entry& a, const Entry& b) const { return a.value != b.value ? a.value > b.value : a.name > b.name; } };

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int x; cin >> x;
    unordered_map<string, long long> usage;
    priority_queue<Entry, vector<Entry>, Low> low;
    auto clean_low = [&] { while (!low.empty()) { auto it = usage.find(low.top().name); if (it != usage.end() && it->second == low.top().value) break; low.pop(); } };
    auto add = [&](const string& name, long long value) { usage[name] = value; low.push({value, name}); };
    while (x--) {
        string command; cin >> command;
        if (command == "feat") { string s; long long p; cin >> s >> p; if (usage.find(s) == usage.end()) add(s, p); }
        else if (command == "fix") { long long p; cin >> p; clean_low(); if (!low.empty()) { auto e = low.top(); add(e.name, e.value + p); } }
        else if (command == "hotfix") { string s; long long p; cin >> s >> p; if (usage.find(s) != usage.end()) add(s, usage[s] + p); }
        else if (command == "deprecate") { string s; cin >> s; usage.erase(s); }
        else { clean_low(); if (low.empty()) cout << "-1\n"; else cout << low.top().name << ' ' << low.top().value << '\n'; }
    }
}
