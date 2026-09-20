from collections import Counter

from ..models import Card, Player, PlayerType


def _straight_progress(cards: list[Card]) -> int:
    """
    현재 카드들이 6장 스트레이트에 얼마나 가까운지 계산한다.

    1~6, 2~7, ... 7~12의 각 구간 중
    현재 보유한 서로 다른 월이 가장 많이 들어가는 구간을 찾는다.
    """
    months = {
        card.month
        for card in cards
    }

    best = 0

    for start_month in range(1, 8):
        window = set(
            range(
                start_month,
                start_month + 6,
            )
        )

        matched = len(
            months & window
        )

        best = max(
            best,
            matched,
        )

    return best


def _ttoi_progress(cards: list[Card]) -> int:
    """
    또이또이(3쌍)에 가까울수록 높은 값을 준다.

    완성된 페어 하나당 2점,
    싱글은 향후 페어 후보이므로 1점.
    """
    counts = Counter(
        card.month
        for card in cards
    )

    progress = 0

    for count in counts.values():
        if count >= 2:
            progress += 2
        else:
            progress += 1

    return progress


def _four_plus_pair_progress(
    cards: list[Card],
) -> int:
    """
    4장 + 2장 족보에 가까운 정도를 계산한다.

    가장 많은 월은 최대 4장까지,
    두 번째 월은 최대 2장까지 기여한다.
    """
    counts = sorted(
        Counter(
            card.month
            for card in cards
        ).values(),
        reverse=True,
    )

    if not counts:
        return 0

    first = min(
        counts[0],
        4,
    )

    second = (
        min(
            counts[1],
            2,
        )
        if len(counts) >= 2
        else 0
    )

    return first + second


def _discard_candidate_score(
    remaining_cards: list[Card],
) -> tuple:
    """
    카드 한 장을 버린 뒤 남는 손패의 가치를 비교한다.

    중수 AI는 어느 한 족보만 고집하지 않고,
    다음 STOP 가능성이 가장 높은 방향을 우선한다.

    비교 요소:
    - 스트레이트 진행도
    - 또이또이 진행도
    - 4+2 진행도
    - 10 이하 방향
    - 60 이상 방향
    - 같은 월 묶음 보존
    """
    months = [
        card.month
        for card in remaining_cards
    ]

    total = sum(months)

    month_counts = Counter(
        months
    )

    straight = (
        _straight_progress(
            remaining_cards
        )
    )

    ttoi = (
        _ttoi_progress(
            remaining_cards
        )
    )

    four_plus_pair = (
        _four_plus_pair_progress(
            remaining_cards
        )
    )

    # 합 10 이하를 노릴 때:
    # 합이 낮을수록 유리하다.
    low_sum_progress = max(
        0,
        60 - total,
    )

    # 합 60 이상을 노릴 때:
    # 합이 높을수록 유리하다.
    high_sum_progress = total

    # 페어/트리플/포카드처럼 이미 묶인 카드를
    # 함부로 깨지 않도록 보정한다.
    grouped_cards = sum(
        count
        for count in month_counts.values()
        if count >= 2
    )

    # 서로 충돌하는 저합/고합 전략을 단순 합산하지 않고
    # 가장 유리한 STOP 방향의 점수를 사용한다.
    route_scores = [
        straight * 18,
        ttoi * 14,
        four_plus_pair * 16,
        low_sum_progress,
        high_sum_progress,
    ]

    best_route = max(
        route_scores
    )

    return (
        best_route,
        grouped_cards,
        straight,
        ttoi,
        four_plus_pair,
    )


def choose_intermediate_discard(
    player: Player,
) -> Card:
    """
    중수 AI가 버릴 카드 1장을 선택한다.

    모든 버림 후보를 하나씩 가정하고,
    버린 뒤 남은 손패가 STOP 족보에
    가장 가까워지는 선택을 고른다.

    동점이면:
    - 높은 월
    - 높은 copy_index
    순으로 버린다.

    상태를 직접 변경하지 않고
    Card 객체만 반환한다.
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 중수 AI 판단을 "
            "사용할 수 있습니다."
        )

    if not player.hand:
        raise ValueError(
            "버릴 수 있는 카드가 없습니다."
        )

    candidates = []

    for discard_card in player.hand:
        remaining_cards = [
            card
            for card in player.hand
            if card.card_id
            != discard_card.card_id
        ]

        hand_score = (
            _discard_candidate_score(
                remaining_cards
            )
        )

        candidates.append(
            (
                hand_score,
                discard_card.month,
                discard_card.copy_index,
                discard_card,
            )
        )

    return max(
        candidates,
        key=lambda item: (
            item[0],
            item[1],
            item[2],
        ),
    )[3]
