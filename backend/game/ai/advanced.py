from collections import Counter

from ..models import Card, Player, PlayerType
from .intermediate import _discard_candidate_score


def _public_month_count(
    month: int,
    player: Player,
    discard_pile: list[Card],
    discard_card: Card,
) -> int:
    """
    고수 AI가 합법적으로 알 수 있는 공개/자기 카드만 세어
    특정 월 카드가 얼마나 드러났는지 계산한다.

    포함:
    - 현재 AI 자신의 손패
    - 이미 공개된 버림패
    - 지금 버리려는 카드

    상대 손패는 절대 참조하지 않는다.
    """
    known_card_ids = {
        card.card_id
        for card in player.hand
    }

    known_card_ids.update(
        card.card_id
        for card in discard_pile
    )

    known_card_ids.add(
        discard_card.card_id
    )

    known_month_cards = []

    for card in player.hand:
        if (
            card.month == month
            and card.card_id in known_card_ids
        ):
            known_month_cards.append(
                card.card_id
            )

    for card in discard_pile:
        if (
            card.month == month
            and card.card_id in known_card_ids
        ):
            known_month_cards.append(
                card.card_id
            )

    if (
        discard_card.month == month
        and discard_card.card_id
        not in known_month_cards
    ):
        known_month_cards.append(
            discard_card.card_id
        )

    return len(
        set(known_month_cards)
    )


def _bbung_safety_score(
    discard_card: Card,
    player: Player,
    discard_pile: list[Card],
) -> int:
    """
    해당 월을 버렸을 때 상대가 뻥할 가능성을
    공개 정보만으로 보수적으로 평가한다.

    화투는 월마다 4장뿐이므로,
    이미 자기 손패/버림패에 많이 보인 월일수록
    상대가 같은 월 2장을 들고 있을 가능성이 낮다.

    점수가 높을수록 안전하다.
    """
    known_count = _public_month_count(
        month=discard_card.month,
        player=player,
        discard_pile=discard_pile,
        discard_card=discard_card,
    )

    if known_count >= 3:
        return 4

    if known_count == 2:
        return 2

    return 0


def choose_advanced_discard(
    player: Player,
    discard_pile: list[Card],
) -> Card:
    """
    고수 AI의 버림패 선택.

    1. 중수 AI와 동일하게 버린 뒤의 족보 진행도를 계산한다.
    2. 비슷한 선택지라면 공개된 카드 수를 이용해
       상대가 뻥하기 어려운 월을 우선한다.
    3. 상대 손패는 참조하지 않는다.

    상태를 변경하지 않고 Card 객체만 반환한다.
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 고수 AI 판단을 "
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

        safety_score = (
            _bbung_safety_score(
                discard_card=discard_card,
                player=player,
                discard_pile=discard_pile,
            )
        )

        candidates.append(
            (
                hand_score,
                safety_score,
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
            item[3],
        ),
    )[4]


def choose_advanced_stop(
    player: Player,
    available_stops,
    score_calculator,
):
    """
    고수 AI가 여러 STOP이 동시에 가능한 경우
    실제 라운드 점수가 가장 낮아지는 STOP을 선택한다.

    예:
    - MINUS_100 + MINUS_200 -> MINUS_200
    - HIGH_SUM + MINUS_100 -> 실제 점수가 더 낮은 쪽
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 고수 AI 판단을 "
            "사용할 수 있습니다."
        )

    if not available_stops:
        return None

    return min(
        available_stops,
        key=lambda stop_type: (
            score_calculator(
                player.hand,
                stop_type,
            )
        ),
    )


def choose_advanced_bbung_cards(
    player: Player,
    discarded_card: Card,
    discard_pile: list[Card],
) -> tuple[list[Card], Card] | None:
    """
    고수 AI의 뻥 카드 선택.

    뻥 자체는 가능한 경우 실행하되,
    여러 선택지가 있으면 다음을 기준으로
    가장 손해가 적은 조합을 고른다.

    - 뻥에 사용할 같은 월 카드 2장
    - 추가로 버릴 카드 1장
    - 뻥 후 남는 손패의 족보 진행도
    - 추가 버림패가 상대에게 뻥을 허용할 위험

    상대 손패는 참조하지 않는다.
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 고수 AI 판단을 "
            "사용할 수 있습니다."
        )

    matching_cards = [
        card
        for card in player.hand
        if (
            card.month
            == discarded_card.month
        )
    ]

    if len(matching_cards) < 2:
        return None

    best_choice = None
    best_score = None

    # 월당 최대 4장이므로 조합 수가 매우 작다.
    for first_index in range(
        len(matching_cards)
    ):
        for second_index in range(
            first_index + 1,
            len(matching_cards),
        ):
            selected_matching = [
                matching_cards[first_index],
                matching_cards[second_index],
            ]

            selected_ids = {
                card.card_id
                for card in selected_matching
            }

            extra_candidates = [
                card
                for card in player.hand
                if (
                    card.card_id
                    not in selected_ids
                )
            ]

            for extra_card in extra_candidates:
                remaining_cards = [
                    card
                    for card in player.hand
                    if card.card_id
                    not in (
                        selected_ids
                        | {extra_card.card_id}
                    )
                ]

                # 빈 손패도 정상적인 뻥 결과가 될 수 있으므로
                # 별도 안전 점수를 사용한다.
                if remaining_cards:
                    hand_score = (
                        _discard_candidate_score(
                            remaining_cards
                        )
                    )
                else:
                    hand_score = (
                        999,
                        0,
                        0,
                        0,
                        0,
                    )

                safety_score = (
                    _bbung_safety_score(
                        discard_card=extra_card,
                        player=player,
                        discard_pile=discard_pile,
                    )
                )

                choice_score = (
                    hand_score,
                    safety_score,
                    extra_card.month,
                    extra_card.copy_index,
                )

                if (
                    best_score is None
                    or choice_score
                    > best_score
                ):
                    best_score = choice_score
                    best_choice = (
                        selected_matching,
                        extra_card,
                    )

    return best_choice


def _known_month_count(
    month: int,
    player: Player,
    discard_pile: list[Card],
) -> int:
    """
    자기 손패와 공개 버림패에서 확인되는
    특정 월 카드 수를 센다.
    """
    known_ids = {
        card.card_id
        for card in player.hand
        if card.month == month
    }

    known_ids.update(
        card.card_id
        for card in discard_pile
        if card.month == month
    )

    return len(known_ids)


def choose_advanced_general_bagaji_month(
    player: Player,
    discard_pile: list[Card],
) -> int | None:
    """
    고수 AI의 일반 바가지 판단.

    선언 조건을 만족하더라도 해당 월 4장이
    이미 자기 손패/공개 버림패에서 모두 확인되면
    더 이상 상대가 그 월을 버릴 수 없으므로
    선언하지 않는다.
    """
    if player.player_type != PlayerType.BOT:
        return None

    if player.bbung_count <= 0:
        return None

    if len(player.hand) != 2:
        return None

    first = player.hand[0]
    second = player.hand[1]

    if first.month != second.month:
        return None

    target_month = first.month

    if (
        _known_month_count(
            target_month,
            player,
            discard_pile,
        )
        >= 4
    ):
        return None

    return target_month


def choose_advanced_bomb_bagaji_month(
    player: Player,
    discard_pile: list[Card],
) -> int | None:
    """
    고수 AI의 폭탄 바가지 판단.

    정확한 3+2 손패에서 2장짜리 월을 대상으로 하되,
    그 월의 나머지 카드가 공개 정보상 모두 소진됐다면
    발동 가능성이 없으므로 선언하지 않는다.
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
        for month, count
        in month_counts.items()
        if count == 3
    ]

    pair_months = [
        month
        for month, count
        in month_counts.items()
        if count == 2
    ]

    if (
        len(bomb_months) != 1
        or len(pair_months) != 1
    ):
        return None

    target_month = pair_months[0]

    if (
        target_month
        == bomb_months[0]
    ):
        return None

    if (
        _known_month_count(
            target_month,
            player,
            discard_pile,
        )
        >= 4
    ):
        return None

    return target_month


def should_advanced_declare_surprise_stop(
    player: Player,
    discard_pile: list[Card],
) -> bool:
    """
    고수 AI의 기습 STOP 위험 판단.

    실제 상대 손패는 보지 않는다.

    - 두 장 합이 3 이하이면 위험을 감수하고 선언.
    - 합이 4~5이면 1~2월 저월 카드가 공개 정보에서
      충분히 많이 소진된 경우에만 선언한다.

    이는 독박 가능성을 줄이기 위한 보수적 휴리스틱이다.
    """
    if player.player_type != PlayerType.BOT:
        return False

    if len(player.hand) != 2:
        return False

    hand_sum = sum(
        card.month
        for card in player.hand
    )

    if hand_sum > 5:
        return False

    if hand_sum <= 3:
        return True

    visible_low_cards = {
        card.card_id
        for card in player.hand
        if card.month <= 2
    }

    visible_low_cards.update(
        card.card_id
        for card in discard_pile
        if card.month <= 2
    )

    return (
        len(visible_low_cards)
        >= 5
    )
