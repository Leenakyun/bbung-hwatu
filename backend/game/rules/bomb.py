from collections import Counter


def get_bomb_months(cards) -> list[int]:
    """
    손패에서 폭탄이 성립한 월을 모두 반환한다.

    같은 월 카드가 3장 이상 있으면 폭탄이다.

    같은 월이 4장인 경우에도
    그중 3장은 폭탄으로 취급한다.

    예:
    3, 3, 3, 5, 2
    -> [3]

    3, 3, 3, 3, 7
    -> [3]

    3, 3, 5, 2, 1
    -> []
    """
    month_counts = Counter(
        card.month
        for card in cards
    )

    return [
        month
        for month, count in month_counts.items()
        if count >= 3
    ]


def calculate_hand_score(cards) -> int:
    """
    폭탄을 반영한 일반 손패 점수를 계산한다.

    같은 월 카드가 3장 이상 있으면
    그중 정확히 3장의 점수를 0점으로 처리한다.

    예:
    3, 3, 3, 5, 2
    -> 7점

    3, 3, 3, 3, 7
    -> 10점
       (3장 폭탄 = 0, 남은 3 + 7)

    1, 2, 3, 4, 5
    -> 15점
    """
    month_counts = Counter(
        card.month
        for card in cards
    )

    score = 0

    for month, count in month_counts.items():
        if count >= 3:
            remaining_count = count - 3

            score += (
                month * remaining_count
            )
        else:
            score += month * count

    return score