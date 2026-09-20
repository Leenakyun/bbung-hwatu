def get_pair_months(cards) -> list[int]:
    """
    현재 카드 목록에서 정확히 2장 존재하는 월을 반환한다.

    이 함수 자체는 단순한 카드 개수 판정용이다.

    예:
    2, 2
    -> [2]

    2, 2, 5, 5
    -> [2, 5]

    주의:
    일반 바가지 선언 가능 여부는
    이 함수만으로 결정하지 않는다.

    일반 바가지는 손패 전체가
    정확히 2장이어야 한다.
    """
    month_counts = {}

    for card in cards:
        month_counts[card.month] = (
            month_counts.get(card.month, 0) + 1
        )

    return [
        month
        for month, count in month_counts.items()
        if count == 2
    ]


def can_declare_general_bagaji(
    player,
    month: int,
) -> bool:
    """
    플레이어가 특정 월에 대해
    일반 바가지를 선언할 수 있는지 판정한다.

    일반 바가지 조건:
    - 이번 라운드에서 최소 한 번 이상 뻥을 했어야 한다.
    - 현재 손패 전체가 정확히 2장이어야 한다.
    - 그 2장이 모두 선언 대상 월이어야 한다.

    예:
    [2, 2]
    -> 2월 일반 바가지 가능

    [2, 2, 7]
    -> 불가능

    [2, 7]
    -> 불가능
    """
    if player.bbung_count <= 0:
        return False

    if len(player.hand) != 2:
        return False

    matching_count = sum(
        1
        for card in player.hand
        if card.month == month
    )

    return matching_count == 2


def get_bomb_months_for_bagaji(
    cards,
) -> list[int]:
    """
    폭탄 바가지 조건에 사용할
    폭탄 월을 반환한다.

    폭탄 바가지에서는
    같은 월 카드가 정확히 3장이어야 한다.

    예:
    [3, 3, 3, 5, 5]
    -> [3]

    [3, 3, 3, 3, 5]
    -> []

    일반 폭탄 점수 규칙과
    폭탄 바가지 선언 규칙은 별개다.
    """
    month_counts = {}

    for card in cards:
        month_counts[card.month] = (
            month_counts.get(card.month, 0) + 1
        )

    return [
        month
        for month, count in month_counts.items()
        if count == 3
    ]


def get_bomb_bagaji_months(
    player,
) -> list[int]:
    """
    현재 플레이어가 폭탄 바가지로
    선언할 수 있는 대상 월을 반환한다.

    폭탄 바가지 조건:
    - 현재 손패 전체가 정확히 5장
    - 한 월이 정확히 3장
    - 다른 한 월이 정확히 2장
    - 3장 월과 2장 월은 서로 달라야 함

    예:
    [3, 3, 3, 5, 5]
    -> [5]

    [3, 3, 3, 5, 7]
    -> []

    [3, 3, 3, 3, 5]
    -> []

    [3, 3, 3, 5, 5, 7]
    -> []
    """
    if len(player.hand) != 5:
        return []

    bomb_months = get_bomb_months_for_bagaji(
        player.hand
    )

    if not bomb_months:
        return []

    pair_months = get_pair_months(
        player.hand
    )

    return [
        pair_month
        for pair_month in pair_months
        if any(
            bomb_month != pair_month
            for bomb_month in bomb_months
        )
    ]


def can_declare_bomb_bagaji(
    player,
    month: int,
) -> bool:
    """
    특정 월에 대해 폭탄 바가지를
    선언할 수 있는지 판정한다.

    폭탄 바가지 조건:
    - 현재 손패가 정확히 5장
    - 정확히 3장인 폭탄 월 존재
    - 그와 다른 월의 카드가 정확히 2장
    - 이전 뻥 이력은 필요하지 않음

    예:
    [3, 3, 3, 5, 5]
    -> 5월 폭탄 바가지 가능
    """
    return month in get_bomb_bagaji_months(
        player
    )