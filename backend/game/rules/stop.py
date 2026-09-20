from collections import Counter
from enum import Enum


class StopType(str, Enum):
    STRAIGHT = "STRAIGHT"
    HIGH_SUM = "HIGH_SUM"
    TTOI_TTOI = "TTOI_TTOI"
    MINUS_100 = "MINUS_100"
    MINUS_200 = "MINUS_200"


def _get_months(cards) -> list[int]:
    return [
        card.month
        for card in cards
    ]


def _has_four_plus_pair(
    cards,
) -> bool:
    """
    6장 중:
    - 같은 월 4장
    - 다른 같은 월 2장

    형태인지 확인한다.
    """
    if len(cards) != 6:
        return False

    counts = Counter(
        _get_months(cards)
    )

    return sorted(
        counts.values()
    ) == [2, 4]


def _has_low_sum(
    cards,
) -> bool:
    """
    6장 월 합계가 10 이하인지 확인한다.
    """
    if len(cards) != 6:
        return False

    return sum(
        _get_months(cards)
    ) <= 10


def _is_straight(
    cards,
) -> bool:
    """
    서로 다른 6개월이 연속되는 스트레이트.
    12 -> 1 순환은 허용하지 않는다.
    """
    if len(cards) != 6:
        return False

    months = sorted(
        _get_months(cards)
    )

    if len(set(months)) != 6:
        return False

    return months == list(
        range(
            months[0],
            months[0] + 6,
        )
    )


def _is_high_sum(
    cards,
) -> bool:
    """
    6장 월 합계가 60 이상.
    """
    if len(cards) != 6:
        return False

    return sum(
        _get_months(cards)
    ) >= 60


def _is_ttoi_ttoi(
    cards,
) -> bool:
    """
    정확히 세 쌍:
    예) 2,2,5,5,9,9
    """
    if len(cards) != 6:
        return False

    counts = Counter(
        _get_months(cards)
    )

    return (
        len(counts) == 3
        and all(
            count == 2
            for count in counts.values()
        )
    )


def get_available_stops(
    cards,
) -> list[StopType]:
    """
    현재 6장 손패에서 선언 가능한
    모든 일반 STOP을 반환한다.

    규칙:
    - STRAIGHT:
      6개의 서로 다른 연속 월
    - HIGH_SUM:
      합계 60 이상
    - TTOI_TTOI:
      2장씩 3쌍
    - MINUS_100:
      4장+2장 조합 또는 합계 10 이하
    - MINUS_200:
      4장+2장 조합이면서 동시에 합계 10 이하

    여러 조건이 동시에 성립할 수 있다.
    """
    if len(cards) != 6:
        return []

    available = []

    if _is_straight(cards):
        available.append(
            StopType.STRAIGHT
        )

    if _is_high_sum(cards):
        available.append(
            StopType.HIGH_SUM
        )

    if _is_ttoi_ttoi(cards):
        available.append(
            StopType.TTOI_TTOI
        )

    has_four_plus_pair = (
        _has_four_plus_pair(cards)
    )

    has_low_sum = (
        _has_low_sum(cards)
    )

    # 둘 중 하나라도 만족하면 -100.
    if (
        has_four_plus_pair
        or has_low_sum
    ):
        available.append(
            StopType.MINUS_100
        )

    # 두 조건을 동시에 만족하면
    # -100에 더해 -200도 함께 선언 가능하다.
    if (
        has_four_plus_pair
        and has_low_sum
    ):
        available.append(
            StopType.MINUS_200
        )

    return available


def calculate_stop_score(
    cards,
    selected_stop_type: StopType,
) -> int:
    """
    선택한 STOP의 점수를 계산한다.

    실제 선언 가능 여부는
    get_available_stops()로 다시 검증한다.
    """
    available_stops = (
        get_available_stops(cards)
    )

    if (
        selected_stop_type
        not in available_stops
    ):
        raise ValueError(
            "현재 손패로 선택한 STOP을 "
            "선언할 수 없습니다."
        )

    months = _get_months(cards)

    if (
        selected_stop_type
        == StopType.STRAIGHT
    ):
        return -sum(months)

    if (
        selected_stop_type
        == StopType.HIGH_SUM
    ):
        return -sum(months)

    if (
        selected_stop_type
        == StopType.TTOI_TTOI
    ):
        return 0

    if (
        selected_stop_type
        == StopType.MINUS_100
    ):
        return -100

    if (
        selected_stop_type
        == StopType.MINUS_200
    ):
        return -200

    raise ValueError(
        f"알 수 없는 STOP 타입입니다: "
        f"{selected_stop_type}"
    )
