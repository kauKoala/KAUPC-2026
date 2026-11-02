import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;

public class Main {
    private static final long INF = Long.MAX_VALUE / 4;

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = in.nextInt();
        int m = in.nextInt();
        int q = in.nextInt();

        long[][] dist = new long[n][n];
        for (int i = 0; i < n; i++) {
            java.util.Arrays.fill(dist[i], INF);
            dist[i][i] = 0;
        }

        for (int e = 0; e < m; e++) {
            int a = in.nextInt() - 1;
            int b = in.nextInt() - 1;
            long c = in.nextLong();
            if (c < dist[a][b]) {
                dist[a][b] = c;
                dist[b][a] = c;
            }
        }

        for (int k = 0; k < n; k++) {
            long[] distK = dist[k];
            for (int i = 0; i < n; i++) {
                long through = dist[i][k];
                if (through >= INF) continue;
                long[] distI = dist[i];
                for (int j = 0; j < n; j++) {
                    long candidate = through + distK[j];
                    if (candidate < distI[j]) distI[j] = candidate;
                }
            }
        }

        StringBuilder out = new StringBuilder();
        long[] toU = new long[n];
        long[] toV = new long[n];
        for (int t = 0; t < q; t++) {
            int type = in.nextInt();
            if (type == 1) {
                int u = in.nextInt() - 1;
                int v = in.nextInt() - 1;
                long w = in.nextLong();
                for (int i = 0; i < n; i++) {
                    toU[i] = dist[i][u];
                    toV[i] = dist[i][v];
                }
                long[] fromU = dist[u].clone();
                long[] fromV = dist[v].clone();
                for (int i = 0; i < n; i++) {
                    long viaU = toU[i] + w;
                    long viaV = toV[i] + w;
                    long[] distI = dist[i];
                    for (int j = 0; j < n; j++) {
                        long candidate = viaU + fromV[j];
                        long other = viaV + fromU[j];
                        if (other < candidate) candidate = other;
                        if (candidate < distI[j]) distI[j] = candidate;
                    }
                }
            } else {
                int a = in.nextInt() - 1;
                int b = in.nextInt() - 1;
                long answer = dist[a][b];
                out.append(answer >= INF ? -1 : answer).append('\n');
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
                if (size == -1) return -1;
            }
            return buffer[pointer++];
        }

        int nextInt() throws IOException {
            return (int) nextLong();
        }

        long nextLong() throws IOException {
            long value = 0;
            byte c = read();
            while (c <= ' ') c = read();
            boolean negative = c == '-';
            if (negative) c = read();
            while (c >= '0' && c <= '9') {
                value = value * 10 + (c - '0');
                c = read();
            }
            return negative ? -value : value;
        }
    }
}
