// TLE 의도: 넣는다/안 넣는다 재귀에서 가지치기 없음 → 2^N 탐색 (Java)
// N이 작을 때는 정답, N이 약 35 이상이면 1초 안에 끝나지 않음
// 채점 시 파일명을 Main.java로 바꿔 제출할 것
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class Main {
    static int n;
    static String[][] cards;
    static int[] picked = new int[100];
    static int cnt = 0;
    static List<int[]> res = new ArrayList<>();

    static boolean ok(String a, String b, String c) {
        return (a.equals(b) && b.equals(c)) || (!a.equals(b) && !b.equals(c) && !a.equals(c));
    }

    static void go(int idx) {
        if (idx == n) {
            if (cnt == 3) {
                boolean good = true;
                for (int a = 0; a < 4 && good; a++)
                    good = ok(cards[picked[0]][a], cards[picked[1]][a], cards[picked[2]][a]);
                if (good) res.add(new int[]{picked[0] + 1, picked[1] + 1, picked[2] + 1});
            }
            return;
        }
        picked[cnt++] = idx;     // 버그: cnt가 3을 넘어도 계속 탐색
        go(idx + 1);
        cnt--;
        go(idx + 1);
    }

    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        n = Integer.parseInt(br.readLine().trim());
        cards = new String[n][];
        for (int i = 0; i < n; i++) {
            StringTokenizer st = new StringTokenizer(br.readLine());
            cards[i] = new String[]{st.nextToken(), st.nextToken(), st.nextToken(), st.nextToken()};
        }
        go(0);
        res.sort((x, y) -> x[0] != y[0] ? x[0] - y[0] : x[1] != y[1] ? x[1] - y[1] : x[2] - y[2]);
        StringBuilder sb = new StringBuilder();
        for (int[] t : res) sb.append(t[0]).append(' ').append(t[1]).append(' ').append(t[2]).append('\n');
        PrintWriter pw = new PrintWriter(new OutputStreamWriter(System.out, StandardCharsets.UTF_8));
        pw.print(res.isEmpty() ? "No triple\n" : sb.toString());
        pw.flush();
    }
}
