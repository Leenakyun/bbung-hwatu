from ..models import (
    AIDifficulty,
    Card,
    Player,
    PlayerType,
)
from ..rules.stop import (
    calculate_stop_score,
    get_available_stops,
)
from .advanced import (
    _bbung_safety_score,
)
from .intermediate import (
    _discard_candidate_score,
)


def _build_unseen_cards(
    player: Player,
    discard_pile: list[Card],
) -> list[Card]:
    """
    타짜 AI가 알 수 없는 카드 후보를 만든다.

    화투 전체 48장에서:
    - 자기 손패
    - 공개된 버림패

    를 제외한다.

    상대 손패와 실제 덱 순서는 보지 않는다.
    따라서 이 목록은 '미지 카드 전체'이지
    실제 다음 드로우 카드 목록이 아니다.
    """
    known_ids = {
        card.card_id
        for card in player.hand
    }

    known_ids.update(
        card.card_id
        for card in discard_pile
    )

    return [
        Card(
            month=month,
            copy_index=copy_index,
        )
        for month in range(1, 13)
        for copy_index in range(1, 5)
        if (
            Card(
                month=month,
                copy_index=copy_index,
            ).card_id
            not in known_ids
        )
    ]


def _next_draw_value(
    cards_after_draw: list[Card],
) -> float:
    """
    다음 한 장을 받았다고 가정했을 때의 가치를 계산한다.

    STOP이 완성되면 실제 STOP 점수를 큰 보너스로 반영하고,
    아니면 중수 AI의 족보 진행도를 사용한다.
    """
    available_stops = (
        get_available_stops(
            cards_after_draw
        )
    )

    if available_stops:
        best_stop_score = min(
            calculate_stop_score(
                cards_after_draw,
                stop_type,
            )
            for stop_type
            in available_stops
        )

        # -200이 -100보다 훨씬 강하게 평가되도록 한다.
        return (
            1000.0
            + float(-best_stop_score) * 4.0
        )

    route_score = (
        _discard_candidate_score(
            cards_after_draw
        )
    )

    # 튜플의 앞 요소일수록 중요하므로
    # 가중치를 둬 하나의 값으로 환산한다.
    return (
        float(route_score[0]) * 10.0
        + float(route_score[1]) * 2.0
        + float(route_score[2])
        + float(route_score[3])
        + float(route_score[4])
    )


def _expected_next_draw_value(
    remaining_cards: list[Card],
    unseen_cards: list[Card],
) -> float:
    """
    모든 미지 카드를 동일 확률의 후보로 보고
    다음 한 장의 평균 기대가치를 계산한다.

    상대 손패가 섞여 있으므로 완전한 확률 계산은 아니지만,
    공개 정보만으로 가능한 보수적 기대값이다.
    """
    if not unseen_cards:
        return 0.0

    total_value = 0.0

    for unseen_card in unseen_cards:
        total_value += (
            _next_draw_value(
                remaining_cards
                + [unseen_card]
            )
        )

    return (
        total_value
        / len(unseen_cards)
    )


def choose_tazza_discard(
    player: Player,
    discard_pile: list[Card],
) -> Card:
    """
    타짜 AI의 버림패 선택.

    고수보다 한 단계 더 깊게:
    1. 버린 직후 손패의 족보 진행도
    2. 다음 한 장을 받았을 때의 평균 기대가치
    3. 추가 버림패의 뻥 안전도
    를 함께 비교한다.

    상대 손패/실제 덱 순서는 절대 참조하지 않는다.
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 타짜 AI 판단을 "
            "사용할 수 있습니다."
        )

    if (
        player.ai_difficulty
        != AIDifficulty.TAZZA
    ):
        raise ValueError(
            "타짜 난이도 플레이어만 "
            "타짜 판단을 사용할 수 있습니다."
        )

    if not player.hand:
        raise ValueError(
            "버릴 수 있는 카드가 없습니다."
        )

    unseen_cards = (
        _build_unseen_cards(
            player,
            discard_pile,
        )
    )

    candidates = []

    for discard_card in player.hand:
        remaining_cards = [
            card
            for card in player.hand
            if (
                card.card_id
                != discard_card.card_id
            )
        ]

        immediate_score = (
            _discard_candidate_score(
                remaining_cards
            )
        )

        expected_value = (
            _expected_next_draw_value(
                remaining_cards,
                unseen_cards,
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
                expected_value,
                immediate_score,
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
            item[4],
        ),
    )[5]


def choose_tazza_stop(
    player: Player,
    available_stops,
    score_calculator,
    round_number: int,
    other_players: list[Player],
):
    """
    타짜 AI의 STOP 판단.

    - 음수 STOP은 즉시 종료하는 쪽을 선택한다.
    - 여러 STOP이 가능하면 가장 낮은 점수를 선택한다.
    - 또이또이 0점만 가능한 경우:
      * 후반부(15라운드 이후)는 안정적으로 STOP
      * 현재 누적점수 선두(가장 낮은 점수)면 STOP
      * 그 외에는 더 좋은 음수 족보를 노리기 위해 계속 진행

    누적점수는 공개 정보이므로 상대 패를 보지 않는다.
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 타짜 AI 판단을 "
            "사용할 수 있습니다."
        )

    if not available_stops:
        return None

    scored = [
        (
            score_calculator(
                player.hand,
                stop_type,
            ),
            stop_type,
        )
        for stop_type in available_stops
    ]

    best_score, best_stop = min(
        scored,
        key=lambda item: item[0],
    )

    if best_score < 0:
        return best_stop

    if round_number >= 15:
        return best_stop

    all_totals = [
        player.total_score,
        *[
            other.total_score
            for other in other_players
            if other.player_id != player.player_id
        ],
    ]

    if (
        player.total_score
        == min(all_totals)
    ):
        return best_stop

    return None


def choose_tazza_bbung_cards(
    player: Player,
    discarded_card: Card,
    discard_pile: list[Card],
) -> tuple[list[Card], Card] | None:
    """
    타짜 AI의 뻥 판단.

    가능한 모든 뻥 조합을 평가하되,
    '뻥 가능 = 무조건 뻥'으로 처리하지 않는다.

    뻥 전 손패의 족보 진행도와
    뻥 후 남는 손패의 진행도를 비교해서
    손패 가치가 크게 무너지면 뻥을 참는다.

    단, 뻥 후 손패가 2장 이하로 줄어
    일반 바가지/기습 STOP 경로가 열리는 경우에는
    공격적인 선택을 허용한다.
    """
    if player.player_type != PlayerType.BOT:
        raise ValueError(
            "AI 플레이어만 타짜 AI 판단을 "
            "사용할 수 있습니다."
        )

    matching_cards = [
        card
        for card in player.hand
        if card.month == discarded_card.month
    ]

    if len(matching_cards) < 2:
        return None

    current_value = (
        _discard_candidate_score(
            player.hand
        )
    )

    best_choice = None
    best_score = None

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
                if card.card_id not in selected_ids
            ]

            for extra_card in extra_candidates:
                removed_ids = (
                    selected_ids
                    | {extra_card.card_id}
                )

                remaining_cards = [
                    card
                    for card in player.hand
                    if card.card_id not in removed_ids
                ]

                if remaining_cards:
                    remaining_value = (
                        _discard_candidate_score(
                            remaining_cards
                        )
                    )
                else:
                    remaining_value = (
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

                strategic_bonus = 0

                if len(remaining_cards) <= 2:
                    strategic_bonus = 50

                choice_score = (
                    remaining_value,
                    strategic_bonus,
                    safety_score,
                    extra_card.month,
                    extra_card.copy_index,
                )

                if (
                    best_score is None
                    or choice_score > best_score
                ):
                    best_score = choice_score
                    best_choice = (
                        selected_matching,
                        extra_card,
                        remaining_value,
                    )

    if best_choice is None:
        return None

    matching, extra_card, remaining_value = (
        best_choice
    )

    # 뻥 후 두 장 이하라면 바가지/기습 STOP 가능성을
    # 고려해 적극적으로 허용한다.
    remaining_count = (
        len(player.hand) - 3
    )

    if remaining_count <= 2:
        return (
            matching,
            extra_card,
        )

    # 주 경로 점수가 크게 떨어지면 뻥을 참는다.
    if (
        remaining_value[0]
        + 8
        < current_value[0]
    ):
        return None

    return (
        matching,
        extra_card,
    )


def _tazza_known_month_count(
    month: int,
    player: Player,
    discard_pile: list[Card],
) -> int:
    """
    타짜 AI가 자기 손패 + 공개 버림패에서
    확인할 수 있는 특정 월 카드 수.
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


def _is_score_leader(
    player: Player,
    players: list[Player],
) -> bool:
    """
    누적점수가 가장 낮은 공동 선두인지 판정한다.
    """
    if not players:
        return True

    best_total = min(
        target.total_score
        for target in players
    )

    return (
        player.total_score
        == best_total
    )


def choose_tazza_general_bagaji_month(
    player: Player,
    discard_pile: list[Card],
    round_number: int,
    players: list[Player],
) -> int | None:
    """
    타짜 AI의 일반 바가지 판단.

    기본 조건:
    - 뻥 이력 있음
    - 현재 손패 정확히 2장
    - 두 장이 같은 월

    전략:
    - 대상 월 4장이 모두 확인됐으면 선언하지 않음.
    - 미공개 카드가 2장 이상이면 선언.
    - 미공개 카드가 1장뿐이면:
      * 15라운드 이후 또는
      * 누적점수 선두가 아닐 때만 선언.
    - 초중반 선두라면 낮은 발동확률의 바가지는 아껴 둔다.
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

    known_count = (
        _tazza_known_month_count(
            target_month,
            player,
            discard_pile,
        )
    )

    unseen_count = max(
        0,
        4 - known_count,
    )

    if unseen_count <= 0:
        return None

    if unseen_count >= 2:
        return target_month

    if round_number >= 15:
        return target_month

    if not _is_score_leader(
        player,
        players,
    ):
        return target_month

    return None


def choose_tazza_bomb_bagaji_month(
    player: Player,
    discard_pile: list[Card],
    round_number: int,
    players: list[Player],
) -> int | None:
    """
    타짜 AI의 폭탄 바가지 판단.

    정확한 3+2 패에서 2장짜리 월을 대상으로 한다.

    폭탄 바가지는 일반 바가지보다 강하게 취급하므로
    대상 월의 미공개 카드가 한 장이라도 남아 있으면
    원칙적으로 선언한다.

    단, 이미 4장이 전부 확인된 죽은 월이면 선언하지 않는다.
    """
    if player.player_type != PlayerType.BOT:
        return None

    if len(player.hand) != 5:
        return None

    counts = {}

    for card in player.hand:
        counts[card.month] = (
            counts.get(card.month, 0) + 1
        )

    bomb_months = [
        month
        for month, count in counts.items()
        if count == 3
    ]

    pair_months = [
        month
        for month, count in counts.items()
        if count == 2
    ]

    if (
        len(bomb_months) != 1
        or len(pair_months) != 1
    ):
        return None

    target_month = pair_months[0]

    if target_month == bomb_months[0]:
        return None

    known_count = (
        _tazza_known_month_count(
            target_month,
            player,
            discard_pile,
        )
    )

    if known_count >= 4:
        return None

    return target_month


def should_tazza_declare_surprise_stop(
    player: Player,
    discard_pile: list[Card],
    round_number: int,
    players: list[Player],
) -> bool:
    """
    타짜 AI의 기습 STOP 판단.

    상대 손패는 보지 않고 다음 공개 정보만 사용한다.
    - 자신의 두 장 합
    - 누적 점수 순위
    - 현재 라운드
    - 공개된 1~2월 카드 수

    전략:
    - 두 장 합이 3 이하:
      * 후반부거나 누적 선두면 적극 선언
      * 그 외에는 저월 카드가 충분히 공개됐을 때만 선언
    - 합이 4~5:
      * 후반부 + 누적 선두 + 저월 카드가 많이 공개된 경우만 선언

    독박 +50 위험 때문에 고수보다 더 상황 의존적으로 움직인다.
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

    visible_low_ids = {
        card.card_id
        for card in player.hand
        if card.month <= 2
    }

    visible_low_ids.update(
        card.card_id
        for card in discard_pile
        if card.month <= 2
    )

    visible_low_count = len(
        visible_low_ids
    )

    is_leader = _is_score_leader(
        player,
        players,
    )

    if hand_sum <= 3:
        if round_number >= 15:
            return True

        if is_leader:
            return True

        return (
            visible_low_count
            >= 4
        )

    return (
        round_number >= 15
        and is_leader
        and visible_low_count >= 5
    )
