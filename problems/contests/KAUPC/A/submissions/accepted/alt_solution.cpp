#include<iostream>
using namespace std;

int main()
{
    string s = "KAUPC";
    int arr[5];
    int i, j;

    for(i = 0; i < 5; i++)
    {
        cin >> arr[i];
    }

    for(i = 0; i < 5; i++)
    {
        for(j = 0; j < 5; j++)
        {
            if(i >= 2 - arr[j] - 1 && i <= 2 - arr[j] + 1) cout << s[j] << s[j];
            else cout << "..";
        }
        cout << '\n';
    }
}
