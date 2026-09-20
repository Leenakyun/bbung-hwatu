from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .deck import Deck
from .models import Card, Player




class GameStatus(str, Enum):
    WAITING = "WAITING"
    DEALER_SELECTION = "DEALER_SELECTION"
    PLAYING = "PLAYING"
    ROUND_END = "ROUND_END"
    TIE_BREAK = "TIE_BREAK"
    GAME_END = "GAME_END"


class RoundEndReason(str, Enum):
    """
    라운드가 종료된 이유.
    """
    NORMAL_STOP = "NORMAL_STOP"
    BAGAJI = "BAGAJI"
    BOMB_BAGAJI = "BOMB_BAGAJI"
    SURPRISE_STOP = "SURPRISE_STOP"
    DECK_EXHAUSTED = "DECK_EXHAUSTED"


class TurnPhase(str, Enum):
    """
    현재 턴의 진행 단계.
    """
    DRAW = "DRAW"
    DISCARD = "DISCARD"
    REACTION = "REACTION"


@dataclass(frozen=True)
class BagajiDeclaration:
    """
    현재 라운드에서 활성화된 일반 바가지 선언 하나.

    player_id:
        바가지를 선언한 플레이어.

    month:
        바가지 대상으로 선언한 월.
    """
    player_id: str
    month: int


@dataclass(frozen=True)
class BombBagajiDeclaration:
    """
    현재 라운드에서 활성화된 폭탄 바가지 선언 하나.

    player_id:
        폭탄 바가지를 선언한 플레이어.

    month:
        상대가 버리기를 기다리는 바가지 대상 월.

    bomb_month:
        폭탄을 구성하고 있는 월.
    """
    player_id: str
    month: int
    bomb_month: int

        

@dataclass
class GameState:
    """
    하나의 게임 전체 상태를 관리한다.
    """

    game_id: str
    players: list[Player]

    round_number: int = 1
    max_rounds: int = 20

    dealer_id: str | None = None

    # 첫 라운드 선 결정 미니게임(밤일낮짱)
    dealer_selection_mode: str | None = None
    dealer_selection_history: list[dict] = field(
        default_factory=list
    )
    dealer_selection_candidate_ids: list[str] = field(
        default_factory=list
    )
    dealer_selection_current_draws: dict[str, Card] = field(
        default_factory=dict
    )
    dealer_selection_round_number: int = 1
    dealer_selection_deck: Deck | None = None

    current_turn_player_id: str | None = None
    turn_phase: TurnPhase | None = None

    last_discarded_card: Card | None = None
    last_discarded_by_player_id: str | None = None

    bbung_candidate_player_ids: list[str] = field(
        default_factory=list
    )
    bbung_reaction_deadline: datetime | None = None

    active_bagaji_declarations: list[
        BagajiDeclaration
    ] = field(default_factory=list)

    active_bomb_bagaji_declarations: list[
        BombBagajiDeclaration
    ] = field(default_factory=list)

    round_winner_id: str | None = None
    round_finalized: bool = False
    deck_reshuffle_used: bool = False
    round_end_reason: RoundEndReason | None = None

    game_winner_ids: list[str] = field(
        default_factory=list
    )

    declared_stop_type: str | None = None

    surprise_stop_dokbak: bool = False

    bagaji_victim_id: str | None = None
    triggered_bagaji_month: int | None = None

    deck: Deck | None = None
    discard_pile: list[Card] = field(default_factory=list)

    status: GameStatus = GameStatus.WAITING

    tie_break_player_ids: list[str] = field(
        default_factory=list
    )

    tie_break_drawn_cards: dict[
        str,
        list[Card],
    ] = field(
        default_factory=dict
    )

    tie_break_current_player_index: int = 0

    tie_break_round_number: int = 0

    tie_break_deck: Deck | None = None

    game_winner_id: str | None = None

    @property
    def deck_id(self) -> str:
        """
        현재 라운드의 덱 식별자를 필요할 때 계산한다.

        예:
        GAME-001 + 1라운드
        -> GAME-001-R01
        """
        return f"{self.game_id}-R{self.round_number:02d}"

    @property
    def bbung_reaction_open(self) -> bool:
        """
        현재 뻥 반응 기회가 열려 있는지 반환한다.

        뻥 가능한 플레이어가 한 명이라도 있으면 True.
        """
        return bool(
            self.bbung_candidate_player_ids
        )


    