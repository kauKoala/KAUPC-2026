import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/** 매 조회마다 전체 기능을 훑는 비효율 풀이. 정답은 맞지만 시간 초과가 나야 한다. */
public class SortEveryIssue {
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int operations = in.nextInt();
        HashMap<String, Long> usage = new HashMap<>();
        StringBuilder out = new StringBuilder();

        for (int t = 0; t < operations; t++) {
            String command = in.nextToken();
            if (command.equals("feat")) {
                String name = in.nextToken();
                long amount = in.nextLong();
                usage.putIfAbsent(name, amount);
            } else if (command.equals("fix")) {
                long amount = in.nextLong();
                Map.Entry<String, Long> target = lowest(usage);
                if (target != null) {
                    usage.put(target.getKey(), target.getValue() + amount);
                }
            } else if (command.equals("hotfix")) {
                String name = in.nextToken();
                long amount = in.nextLong();
                Long current = usage.get(name);
                if (current != null) {
                    usage.put(name, current + amount);
                }
            } else if (command.equals("deprecate")) {
                usage.remove(in.nextToken());
            } else {
                Map.Entry<String, Long> target = lowest(usage);
                if (target == null) {
                    out.append(-1).append('\n');
                } else {
                    out.append(target.getKey()).append(' ').append(target.getValue()).append('\n');
                }
            }
        }
        System.out.print(out);
    }

    private static Map.Entry<String, Long> lowest(HashMap<String, Long> usage) {
        Map.Entry<String, Long> best = null;
        for (Map.Entry<String, Long> entry : usage.entrySet()) {
            if (best == null
                    || entry.getValue() < best.getValue()
                    || (entry.getValue().equals(best.getValue()) && entry.getKey().compareTo(best.getKey()) < 0)) {
                best = entry;
            }
        }
        return best;
    }

    private static final class FastReader {
        private final DataInputStream stream;
        private final byte[] buffer = new byte[1 << 16];
        private final StringBuilder token = new StringBuilder();
        private int pointer = 0;
        private int size = 0;

        FastReader(InputStream input) {
            stream = new DataInputStream(input);
        }

        private int read() throws IOException {
            if (pointer == size) {
                size = stream.read(buffer, 0, buffer.length);
                pointer = 0;
                if (size == -1) {
                    return -1;
                }
            }
            return buffer[pointer++];
        }

        String nextToken() throws IOException {
            token.setLength(0);
            int c = read();
            while (c != -1 && c <= ' ') {
                c = read();
            }
            while (c > ' ') {
                token.append((char) c);
                c = read();
            }
            return token.toString();
        }

        int nextInt() throws IOException {
            return (int) nextLong();
        }

        long nextLong() throws IOException {
            int c = read();
            while (c != -1 && c <= ' ') {
                c = read();
            }
            long value = 0;
            while (c >= '0' && c <= '9') {
                value = value * 10 + (c - '0');
                c = read();
            }
            return value;
        }
    }
}
