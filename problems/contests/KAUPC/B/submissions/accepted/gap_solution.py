import sys
input = sys.stdin.readline

# 3장의 카드가 세트의 조건을 만족하는지 확인하는 함수
def is_set(card1, card2, card3) :
    for i in range(4) :
        a = card1[i]
        b = card2[i]
        c = card3[i]

        # 모두 같지도 않고, 모두 다르지도 않다면 세트가 아님.
        if not ((a == b and b == c) or (a != b and b != c and a != c)) :
            return False
    return True

n = int(input())
cards = [list(input().split()) for _ in range(n)]

sets = []
n = len(cards)

# 3중 for문을 사용하여 3장을 고르는 조합 구현
# 인덱스가 겹치지 않도록 시작점과 끝점을 조정
for i in range(n - 2) :
    for j in range(i + 1, n - 1) :
        for k in range(j + 1, n) :
            # 선택된 3장의 카드가 결합 조건에 맞는지 확인
            if is_set(cards[i], cards[j], cards[k]) :
                sets.append([i+1, j+1, k+1])

# 결과 출력
# 조건을 만족하는 트리플이 없다면 No triple 출력
if not sets:
    print("No triple")
else:
    # 세트 목록 출력
    for i in range(len(sets)) :
        print(sets[i][0], sets[i][1], sets[i][2], " ")
