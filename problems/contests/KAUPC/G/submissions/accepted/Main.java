import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.PriorityQueue;

public class Main {
    private static final class Entry {
        final long value;
        final String name;

        Entry(long value, String name) {
            this.value = value;
            this.name = name;
        }
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int operations = in.nextInt();

        HashMap<String, Long> usage = new HashMap<>();
        PriorityQueue<Entry> heap = new PriorityQueue<>((a, b) -> {
            if (a.value != b.value) {
                return Long.compare(a.value, b.value);
            }
            return a.name.compareTo(b.name);
        });
        StringBuilder out = new StringBuilder();

        for (int t = 0; t < operations; t++) {
            String command = in.nextToken();
            if (command.equals("feat")) {
                String name = in.nextToken();
                long amount = in.nextLong();
                if (!usage.containsKey(name)) {
                    usage.put(name, amount);
                    heap.add(new Entry(amount, name));
                }
            } else if (command.equals("fix")) {
                long amount = in.nextLong();
                discardStale(heap, usage);
                if (heap.isEmpty()) {
                    continue;
                }
                Entry top = heap.poll();
                long updated = top.value + amount;
                usage.put(top.name, updated);
                heap.add(new Entry(updated, top.name));
            } else if (command.equals("hotfix")) {
                String name = in.nextToken();
                long amount = in.nextLong();
                Long current = usage.get(name);
                if (current != null) {
                    long updated = current + amount;
                    usage.put(name, updated);
                    heap.add(new Entry(updated, name));
                }
            } else if (command.equals("deprecate")) {
                usage.remove(in.nextToken());
            } else {
                discardStale(heap, usage);
                if (heap.isEmpty()) {
                    out.append(-1).append('\n');
                } else {
                    Entry top = heap.peek();
                    out.append(top.name).append(' ').append(top.value).append('\n');
                }
            }
        }
        System.out.print(out);
    }

    private static void discardStale(PriorityQueue<Entry> heap, HashMap<String, Long> usage) {
        while (!heap.isEmpty()) {
            Entry top = heap.peek();
            Long current = usage.get(top.name);
            if (current != null && current == top.value) {
                return;
            }
            heap.poll();
        }
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
            while (c == ' ' || c == '\n' || c == '\r') {
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
