#include<iostream>
#include<set>
#include<map>
using namespace std;

set<pair<long long, string>> point_set;
map<string, long long> name_map;

int main()
{
    int q;
    string a, b;
    long long c;
    string name;
    long long point;

    cin.tie(NULL);
    ios::sync_with_stdio(false);

    cin >> q;
    while(q--)
    {
        cin >> a;

        if(a.compare("feat") == 0)
        {
            cin >> b >> c;

            if(name_map.find(b) != name_map.end()) continue;

            name_map[b] = c;
            point_set.insert(make_pair(c, b));
        }
        else if(a.compare("fix") == 0)
        {
            cin >> c;

            if(point_set.empty()) continue;

            name = point_set.begin()->second;
            point = point_set.begin()->first;
            point_set.erase(point_set.begin());

            name_map[name] = point + c;
            point_set.insert(make_pair(point + c, name));
        }
        else if(a.compare("hotfix") == 0)
        {
            cin >> b >> c;

            if(name_map.find(b) == name_map.end()) continue;

            name = b;
            point = name_map[name];

            point_set.erase(point_set.find(make_pair(point, name)));

            point_set.insert(make_pair(point + c, name));
            name_map[name] += c;

        }
        else if(a.compare("deprecate") == 0)
        {
            cin >> b;

            if(name_map.find(b) == name_map.end()) continue;

            name = b;
            point = name_map[name];

            point_set.erase(point_set.find(make_pair(point, name)));
            name_map.erase(name);
        }
        else if(a.compare("issue") == 0)
        {
            if(point_set.empty())
            {
                cout << -1 << '\n';
                continue;
            }

            name = point_set.begin()->second;
            point = point_set.begin()->first;

            cout << name << ' ' << point << '\n';
        }
        else return 1;
    }
}
