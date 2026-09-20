from .deck import Deck
from .models import Player


def deal_initial_cards(
    deck: Deck,
    players: list[Player],
    dealer_id: str,
) -> None:
    """
    라운드 시작 시 카드를 분배한다.

    선(dealer): 6장
    나머지 플레이어: 5장
    """

    for player in players:
        card_count = 6 if player.player_id == dealer_id else 5

        for _ in range(card_count):
            card = deck.draw()
            player.hand.append(card)


def determine_initial_dealer_with_history(
    players: list[Player],
    is_night: bool,
) -> tuple[str, list[dict]]:
    """
    첫 라운드 선을 밤일낮짱으로 결정하면서
    브라우저에 보여 줄 모든 추첨 라운드를 기록한다.

    NIGHT:
        가장 낮은 월이 승리.

    DAY:
        가장 높은 월이 승리.

    같은 월 동점:
        동점자들만 새 선 결정 덱으로 재추첨.

    선 결정용 덱은 매 추첨 라운드마다 새 48장 덱을 사용하며,
    실제 본게임 덱과 완전히 별개다.
    """
    if not players:
        raise ValueError(
            "선 결정에 필요한 플레이어가 없습니다."
        )

    candidates = list(players)
    history = []
    draw_round = 1

    while True:
        dealer_deck = Deck()
        dealer_deck.shuffle()

        draws = {
            player.player_id:
                dealer_deck.draw()
            for player in candidates
        }

        target_month = (
            min(
                card.month
                for card in draws.values()
            )
            if is_night
            else max(
                card.month
                for card in draws.values()
            )
        )

        winner_ids = [
            player.player_id
            for player in candidates
            if (
                draws[player.player_id].month
                == target_month
            )
        ]

        history.append(
            {
                "round": draw_round,
                "draws": draws,
                "winner_ids": list(
                    winner_ids
                ),
            }
        )

        if len(winner_ids) == 1:
            return (
                winner_ids[0],
                history,
            )

        winner_id_set = set(
            winner_ids
        )

        candidates = [
            player
            for player in candidates
            if (
                player.player_id
                in winner_id_set
            )
        ]

        draw_round += 1


def determine_initial_dealer(
    players: list[Player],
    is_night: bool,
) -> str:
    """
    기존 호출 호환용.
    선 ID만 필요할 때 사용한다.
    """
    dealer_id, _history = (
        determine_initial_dealer_with_history(
            players=players,
            is_night=is_night,
        )
    )

    return dealer_id
