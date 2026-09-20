from collections import Counter

from .state import GameState


class GameCardIntegrityError(Exception):
    """
    게임 전체의 카드 무결성이 깨졌을 때 발생하는 예외.
    """
    pass


def get_all_cards(state: GameState):
    """
    현재 게임에 존재하는 모든 카드를 한 목록으로 모은다.

    현재 카드가 존재할 수 있는 영역:
    - 덱
    - 각 플레이어 손패
    - 버림패

    추후 temporary_zone 같은 영역이 추가되면
    이 함수에 포함시킨다.
    """
    cards = []

    if state.deck is not None:
        cards.extend(
            state.deck.cards
        )

    for player in state.players:
        cards.extend(
            player.hand
        )

    cards.extend(
        state.discard_pile
    )

    return cards


def validate_game_card_integrity(
    state: GameState,
) -> None:
    """
    게임 전체 카드 무결성을 검사한다.

    검사 항목:
    1. 전체 카드 수가 정확히 48장인가
    2. 모든 card_id가 고유한가
    3. 각 월이 정확히 4장씩 존재하는가
    4. month가 1~12 범위인가
    5. copy_index가 1~4 범위인가
    """
    cards = get_all_cards(state)

    # -------------------------------------------------
    # 1. 전체 카드 수
    # -------------------------------------------------

    if len(cards) != 48:
        raise GameCardIntegrityError(
            f"게임 전체 카드 수 오류: "
            f"{len(cards)}장 (정상: 48장)"
        )

    # -------------------------------------------------
    # 2. card_id 중복 검사
    # -------------------------------------------------

    card_ids = [
        card.card_id
        for card in cards
    ]

    if len(card_ids) != len(set(card_ids)):
        duplicated_ids = [
            card_id
            for card_id, count
            in Counter(card_ids).items()
            if count > 1
        ]

        raise GameCardIntegrityError(
            f"중복 card_id 발견: "
            f"{duplicated_ids}"
        )

    # -------------------------------------------------
    # 3. 월별 카드 수
    # -------------------------------------------------

    month_counts = Counter(
        card.month
        for card in cards
    )

    for month in range(1, 13):
        count = month_counts.get(
            month,
            0,
        )

        if count != 4:
            raise GameCardIntegrityError(
                f"{month}월 카드 수 오류: "
                f"{count}장 (정상: 4장)"
            )

    # -------------------------------------------------
    # 4. month 범위
    # -------------------------------------------------

    for card in cards:
        if not 1 <= card.month <= 12:
            raise GameCardIntegrityError(
                f"잘못된 month: "
                f"{card.month}"
            )

    # -------------------------------------------------
    # 5. copy_index 범위
    # -------------------------------------------------

    for card in cards:
        if not 1 <= card.copy_index <= 4:
            raise GameCardIntegrityError(
                f"잘못된 copy_index: "
                f"{card.card_id}"
            )