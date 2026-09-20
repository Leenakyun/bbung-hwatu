def calculate_two_card_sum(cards) -> int:
    """
    기습 STOP 판정용 두 장의 월 합계를 계산한다.
    """
    if len(cards) != 2:
        raise ValueError(
            "기습 STOP 판정은 손패 2장이 필요합니다."
        )

    return sum(
        card.month
        for card in cards
    )


def count_bbung_players(players) -> int:
    """
    현재 라운드에서 한 번 이상 뻥한 플레이어 수를 센다.
    """
    return sum(
        1
        for player in players
        if player.bbung_count > 0
    )


def get_required_bbung_player_count(
    player_count: int,
) -> int:
    """
    기습 STOP에 필요한 최소 뻥 플레이어 수.

    3인:
        본인 포함 2명 이상

    4~6인:
        본인 포함 3명 이상
    """
    if player_count == 3:
        return 2

    if 4 <= player_count <= 6:
        return 3

    raise ValueError(
        f"지원하지 않는 플레이어 수입니다: "
        f"{player_count}"
    )


def can_declare_surprise_stop(
    player,
    players,
) -> bool:
    """
    플레이어가 기습 STOP의 패 조건과
    뻥 인원 조건을 만족하는지 판정한다.

    주의:
    '본인 턴인지' 여부는 GameEngine에서 검사한다.

    조건:
    - 손패가 정확히 2장
    - 두 장의 월 합계가 5 이하
    - 선언자 본인도 이번 라운드에 뻥한 적이 있어야 함
    - 전체 뻥 플레이어 수가 기준 이상
    """
    if len(player.hand) != 2:
        return False

    if calculate_two_card_sum(player.hand) > 5:
        return False

    if player.bbung_count <= 0:
        return False

    required_count = (
        get_required_bbung_player_count(
            len(players)
        )
    )

    bbung_player_count = (
        count_bbung_players(players)
    )

    return (
        bbung_player_count
        >= required_count
    )

def has_surprise_stop_dokbak(
    player,
    players,
    hand_score_calculator,
) -> bool:
    """
    기습 STOP 독박 여부를 판정한다.

    기습 STOP 선언자의 2장 합보다
    다른 플레이어의 현재 손패 점수가 더 낮으면
    독박이 발생한다.

    다른 플레이어 중 한 명이라도 더 낮으면 True.
    """
    declarer_score = calculate_two_card_sum(
        player.hand
    )

    for other_player in players:
        if other_player.player_id == player.player_id:
            continue

        other_score = hand_score_calculator(
            other_player.hand
        )

        if other_score < declarer_score:
            return True

    return False