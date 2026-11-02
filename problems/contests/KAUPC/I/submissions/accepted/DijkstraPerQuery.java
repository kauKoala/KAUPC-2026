import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.PriorityQueue;

/** 2번 쿼리마다 다익스트라를 새로 도는 풀이. 시간 제한 5초 안에 통과해야 한다. */
public class DijkstraPerQuery {
    private static final long INF = Long.MAX_VALUE / 4;

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = in.nextInt();
        int m = in.nextInt();
        int q = in.nextInt();

        List<List<long[]>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            graph.add(new ArrayList<>());
        }
        for (int e = 0; e < m; e++) {
            int a = in.nextInt() - 1;
            int b = in.nextInt() - 1;
            long c = in.nextLong();
            graph.get(a).add(new long[] {b, c});
            graph.get(b).add(new long[] {a, c});
        }

        StringBuilder out = new StringBuilder();
        long[] best = new long[n];
        for (int t = 0; t < q; t++) {
            int kind = in.nextInt();
            if (kind == 1) {
                int u = in.nextInt() - 1;
                int v = in.nextInt() - 1;
                long w = in.nextLong();
                graph.get(u).add(new long[] {v, w});
                graph.get(v).add(new long[] {u, w});
            } else {
                int start = in.nextInt() - 1;
                int goal = in.nextInt() - 1;
                Arrays.fill(best, INF);
                best[start] = 0;
                PriorityQueue<long[]> queue = new PriorityQueue<>((x, y) -> Long.compare(x[0], y[0]));
                queue.add(new long[] {0, start});
                while (!queue.isEmpty()) {
                    long[] top = queue.poll();
                    int node = (int) top[1];
                    if (top[0] > best[node]) {
                        continue;
                    }
                    for (long[] edge : graph.get(node)) {
                        int next = (int) edge[0];
                        long candidate = top[0] + edge[1];
                        if (candidate < best[next]) {
                            best[next] = candidate;
                            queue.add(new long[] {candidate, next});
                        }
                    }
                }
                out.append(best[goal] >= INF ? -1 : best[goal]).append('\n');
            }
        }
        System.out.print(out);
    }

    private static final class FastReader {
        private final DataInputStream stream;
        private final byte[] buffer = new byte[1 << 16];
        private int pointer = 0;
        private int size = 0;

        FastReader(InputStream input) {
            stream = new DataInputStream(input);
        }

        private byte read() throws IOException {
            if (pointer == size) {
                size = stream.read(buffer, 0, buffer.length);
                pointer = 0;
                if (size == -1) {
                    return -1;
                }
            }
            return buffer[pointer++];
        }

        int nextInt() throws IOException {
            return (int) nextLong();
        }

        long nextLong() throws IOException {
            long value = 0;
            byte c = read();
            while (c <= ' ') {
                c = read();
            }
            boolean negative = c == '-';
            if (negative) {
                c = read();
            }
            while (c >= '0' && c <= '9') {
                value = value * 10 + (c - '0');
                c = read();
            }
            return negative ? -value : value;
        }
    }
}
