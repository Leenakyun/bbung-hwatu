from ..models import Card, Player, PlayerType
from collections import Counter


def choose_beginner_discard(
    player: Player,
) -> Card:
    """
    초보 AI가 버릴 카드 1장을 선택한다.

    전략:
    1. 단독 월 카드를 가장 먼저 버린다.
    2. 단독 카드가 없으면 페어에서 버린다.
    3. 그것도 없으면 폭탄 월에서 버린다.
    4. 같은 조건에서는 월 숫자가 큰 카드를 버린다.

    상태를 직접 변경하지 않고
    선택한 Card 객체만 반환한다.
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 초보 AI 판단을 "
            "사용할 수 있습니다."
        )

    if not player.hand:
        raise ValueError(
            "버릴 수 있는 카드가 없습니다."
        )

    month_counts = Counter(
        card.month
        for card in player.hand
    )

    def discard_priority(
        card: Card,
    ) -> tuple[int, int, int]:
        count = month_counts[card.month]

        if count == 1:
            group_priority = 3

        elif count == 2:
            group_priority = 2

        else:
            group_priority = 1

        return (
            group_priority,
            card.month,
            card.copy_index,
        )

    return max(
        player.hand,
        key=discard_priority,
    )

def choose_beginner_bbung_cards(
    player: Player,
    discarded_card: Card,
) -> tuple[list[Card], Card] | None:
    """
    초보 AI가 뻥에 사용할 카드들을 선택한다.

    전략:
    - 마지막 버림패와 같은 월 카드 2장을 사용
    - 남은 카드 중 월 숫자가 가장 큰 카드 1장을
      추가 버림패로 선택

    뻥할 수 없으면 None 반환.
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 초보 AI 판단을 "
            "사용할 수 있습니다."
        )

    matching_cards = [
        card
        for card in player.hand
        if card.month == discarded_card.month
    ]

    if len(matching_cards) < 2:
        return None

    selected_matching_cards = (
        matching_cards[:2]
    )

    matching_card_ids = {
        card.card_id
        for card in selected_matching_cards
    }

    extra_candidates = [
        card
        for card in player.hand
        if card.card_id not in matching_card_ids
    ]

    if not extra_candidates:
        return None

    extra_discard_card = max(
        extra_candidates,
        key=lambda card: (
            card.month,
            card.copy_index,
        ),
    )

    return (
        selected_matching_cards,
        extra_discard_card,
    )

def choose_beginner_general_bagaji_month(
    player: Player,
) -> int | None:
    """
    초보 AI가 일반 바가지로 선언할 월 하나를 선택한다.

    조건:
    - BOT 플레이어
    - 이번 라운드에 최소 1회 이상 뻥
    - 현재 손패에 같은 월 카드가 정확히 2장 존재

    여러 페어가 있으면 초보 AI는
    가장 높은 월 하나만 선택한다.

    실제 선언은 하지 않고 월만 반환한다.
    """
    if player.player_type != PlayerType.BOT:
        return None

    if player.bbung_count <= 0:
        return None

    month_counts = Counter(
        card.month
        for card in player.hand
    )

    pair_months = [
        month
        for month, count in month_counts.items()
        if count == 2
    ]

    if not pair_months:
        return None

    return max(pair_months)


def choose_beginner_general_bagaji_month(
    player: Player,
) -> int | None:
    """
    초보 AI가 일반 바가지로 선언할 월을 반환한다.

    조건:
    - BOT
    - 뻥 이력 있음
    - 손패 정확히 2장
    - 두 카드가 같은 월

    실제 선언은 하지 않는다.
    """
    if player.player_type != PlayerType.BOT:
        return None

    if player.bbung_count <= 0:
        return None

    if len(player.hand) != 2:
        return None

    first_card = player.hand[0]
    second_card = player.hand[1]

    if first_card.month != second_card.month:
        return None

    return first_card.month


def choose_beginner_bomb_bagaji_month(
    player: Player,
) -> int | None:
    """
    초보 AI가 폭탄 바가지로 선언할
    대상 월(2장짜리 월)을 반환한다.

    조건:
    - BOT
    - 손패 정확히 5장
    - 정확한 3+2 구성

    실제 선언은 하지 않는다.
    """
    if player.player_type != PlayerType.BOT:
        return None

    if len(player.hand) != 5:
        return None

    month_counts = Counter(
        card.month
        for card in player.hand
    )

    bomb_months = [
        month
        for month, count in month_counts.items()
        if count == 3
    ]

    pair_months = [
        month
        for month, count in month_counts.items()
        if count == 2
    ]

    if len(bomb_months) != 1:
        return None

    if len(pair_months) != 1:
        return None

    if bomb_months[0] == pair_months[0]:
        return None

    return pair_months[0]