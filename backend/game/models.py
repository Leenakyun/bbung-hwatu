from dataclasses import dataclass, field
from enum import Enum



class AIDifficulty(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    TAZZA = "TAZZA"

    @property
    def display_name(self) -> str:
        names = {
            AIDifficulty.BEGINNER: "초보",
            AIDifficulty.INTERMEDIATE: "중수",
            AIDifficulty.ADVANCED: "고수",
            AIDifficulty.TAZZA: "타짜",
        }

        return names[self]



class PlayerType(str, Enum):
    HUMAN = "HUMAN"
    BOT = "BOT"


@dataclass(frozen=True)
class Card:
    """
    화투 카드 한 장을 나타낸다.

    month:
        카드의 월 숫자. 1~12.

    copy_index:
        같은 월의 카드 4장을 구분하기 위한 번호. 1~4.
    """
    month: int
    copy_index: int

    @property
    def card_id(self) -> str:
        """
        카드 고유 ID를 반환한다.

        예:
        1월 1번 카드  -> 01-01
        3월 2번 카드  -> 03-02
        12월 4번 카드 -> 12-04
        """
        return f"{self.month:02d}-{self.copy_index:02d}"


@dataclass
class Player:
    player_id: str
    nickname: str
    player_type: PlayerType

    # 같은 온라인 브라우저 탭의 중복 참가 요청 식별용.
    # SOLO/AI 플레이어는 None.
    client_id: str | None = None

    hand: list[Card] = field(default_factory=list)

    ai_difficulty: AIDifficulty | None = None

    round_score: int = 0
    total_score: int = 0

    bbung_count: int = 0
    bbung_months: list[int] = field(
        default_factory=list
    )