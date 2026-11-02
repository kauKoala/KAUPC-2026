#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TABLE_SIZE (1u << 21)
#define TABLE_MASK (TABLE_SIZE - 1)
#define MAX_FEATURES 600005
#define MAX_HEAP 1300005

typedef struct { char name[21]; long long value; unsigned version; int active; } Feature;
typedef struct { long long value; int id; unsigned version; } HeapItem;

static Feature features[MAX_FEATURES];
static int table[TABLE_SIZE], feature_count;
static HeapItem low[MAX_HEAP];
static int low_size;

static unsigned hash_name(const char *s) {
    unsigned h = 2166136261u;
    while (*s) h = (h ^ (unsigned char)*s++) * 16777619u;
    return h;
}

static int id_for(const char *name) {
    unsigned slot = hash_name(name) & TABLE_MASK;
    while (table[slot]) {
        int id = table[slot] - 1;
        if (!strcmp(features[id].name, name)) return id;
        slot = (slot + 1) & TABLE_MASK;
    }
    int id = feature_count++;
    strcpy(features[id].name, name);
    table[slot] = id + 1;
    return id;
}

static int low_before(HeapItem a, HeapItem b) {
    if (a.value != b.value) return a.value < b.value;
    return strcmp(features[a.id].name, features[b.id].name) < 0;
}
static void push(HeapItem *heap, int *size, HeapItem item, int (*before)(HeapItem, HeapItem)) {
    int at = ++*size;
    while (at > 1 && before(item, heap[at / 2])) { heap[at] = heap[at / 2]; at /= 2; }
    heap[at] = item;
}
static HeapItem pop(HeapItem *heap, int *size, int (*before)(HeapItem, HeapItem)) {
    HeapItem top = heap[1], tail = heap[(*size)--];
    int at = 1;
    while (at * 2 <= *size) {
        int child = at * 2;
        if (child + 1 <= *size && before(heap[child + 1], heap[child])) ++child;
        if (before(tail, heap[child])) break;
        heap[at] = heap[child]; at = child;
    }
    if (*size) heap[at] = tail;
    return top;
}
static int fresh(HeapItem item) {
    Feature *f = &features[item.id];
    return f->active && f->version == item.version && f->value == item.value;
}
static void clean(HeapItem *heap, int *size, int (*before)(HeapItem, HeapItem)) {
    while (*size && !fresh(heap[1])) pop(heap, size, before);
}
static void add(int id, long long value) {
    Feature *f = &features[id];
    f->active = 1; f->value = value; ++f->version;
    HeapItem item = {value, id, f->version};
    push(low, &low_size, item, low_before);
}
static int next_token(char *s) { return scanf("%20s", s) == 1; }

int main(void) {
    int operations;
    if (scanf("%d", &operations) != 1) return 0;
    char command[21], a[21]; long long p;
    while (operations-- && next_token(command)) {
        if (!strcmp(command, "feat")) {
            scanf("%20s %lld", a, &p); int id = id_for(a); if (!features[id].active) add(id, p);
        } else if (!strcmp(command, "fix")) {
            scanf("%lld", &p); clean(low, &low_size, low_before); if (low_size) add(low[1].id, low[1].value + p);
        } else if (!strcmp(command, "hotfix")) {
            scanf("%20s %lld", a, &p); int id = id_for(a); if (features[id].active) add(id, features[id].value + p);
        } else if (!strcmp(command, "deprecate")) {
            scanf("%20s", a); int id = id_for(a); if (features[id].active) { features[id].active = 0; ++features[id].version; }
        } else {
            clean(low, &low_size, low_before);
            if (!low_size) puts("-1"); else printf("%s %lld\n", features[low[1].id].name, low[1].value);
        }
    }
    return 0;
}
