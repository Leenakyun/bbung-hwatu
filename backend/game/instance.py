from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .state import GameState


class GameMode(str, Enum):
    SOLO_AI = "SOLO_AI"
    ONLINE = "ONLINE"


@dataclass
class GameInstance:
    """
    실제 게임방 하나를 나타낸다.

    각 GameInstance는 자기만의 GameState를 가진다.
    """

    game_id: str
    mode: GameMode
    state: GameState

    owner_id: str | None = None
    max_players: int | None = None
    is_private: bool = False
    room_password_hash: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_activity_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

