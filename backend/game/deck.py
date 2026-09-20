import random
from collections import Counter

from .models import Card


class DeckValidationError(Exception):
    """화투 덱의 무결성이 깨졌을 때 발생하는 예외."""
    pass


class Deck:
    TOTAL_CARDS = 48
    MONTHS = range(1, 13)
    COPIES_PER_MONTH = 4

    def __init__(self) -> None:
        self.cards: list[Card] = self._create_cards()
        self.validate()

    def _create_cards(self) -> list[Card]:
        """
        1월부터 12월까지 각각 정확히 4장씩 생성한다.
        """
        return [
            Card(month=month, copy_index=copy_index)
            for month in self.MONTHS
            for copy_index in range(1, self.COPIES_PER_MONTH + 1)
        ]

    def shuffle(self) -> None:
        """
        카드 구성은 바꾸지 않고 순서만 섞는다.
        """
        random.shuffle(self.cards)

    def draw(self) -> Card:
        """
        덱에서 카드 한 장을 뽑는다.
        """
        if not self.cards:
            raise IndexError("더 이상 뽑을 카드가 없습니다.")

        return self.cards.pop()

    def validate(self) -> None:
        """
        덱이 정상적인 48장인지 검사한다.
        """

        # 전체 카드 수
        if len(self.cards) != self.TOTAL_CARDS:
            raise DeckValidationError(
                f"잘못된 카드 수: {len(self.cards)}장 "
                f"(정상: {self.TOTAL_CARDS}장)"
            )

        # 월별 카드 수
        month_counts = Counter(card.month for card in self.cards)

        for month in self.MONTHS:
            count = month_counts.get(month, 0)

            if count != self.COPIES_PER_MONTH:
                raise DeckValidationError(
                    f"{month}월 카드 수 오류: "
                    f"{count}장 (정상: {self.COPIES_PER_MONTH}장)"
                )

        # card_id 중복 검사
        card_ids = [card.card_id for card in self.cards]

        if len(card_ids) != len(set(card_ids)):
            raise DeckValidationError(
                "동일한 card_id가 중복으로 존재합니다."
            )