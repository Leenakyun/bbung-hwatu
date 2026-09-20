def get_bbung_cards(cards, discarded_card):
    """
    상대가 버린 카드와 같은 월의 카드를
    현재 손패에서 찾아 반환한다.

    뻥 선언에는 같은 월 카드가 최소 2장 필요하다.
    """
    return [
        card
        for card in cards
        if card.month == discarded_card.month
    ]


def can_declare_bbung(
    cards,
    discarded_card,
) -> bool:
    """
    상대가 버린 카드에 대해
    현재 손패로 뻥 선언이 가능한지 판정한다.

    조건:
    - 손패에 버린 카드와 같은 월이 2장 이상 있어야 한다.
    """
    matching_cards = get_bbung_cards(
        cards,
        discarded_card,
    )

    return len(matching_cards) >= 2