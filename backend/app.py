import json
import logging
import os
import queue
import re
import threading
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, timezone
import time

from auth import AuthError, AuthStore
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from flask import (
    Flask,
    Response,
    jsonify,
    request,
    send_from_directory,
    stream_with_context,
)

from game.deck import Deck
from game.engine import GameEngine
from game.instance import GameInstance, GameMode
from game.manager import GameManager
from game.realtime import OnlineRealtimeHub
from game.models import (
    AIDifficulty,
    Player,
    PlayerType,
)
from game.setup import (
    deal_initial_cards,
    determine_initial_dealer,
    determine_initial_dealer_with_history,
)
from game.state import (
    GameState,
    GameStatus,
    TurnPhase,
)


app = Flask(__name__)
manager = GameManager()

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.dirname(
    BASE_DIR
)

FRONTEND_DIR = os.path.join(
    PROJECT_ROOT,
    "frontend",
)

RAILWAY_VOLUME_MOUNT_PATH = os.environ.get(
    "RAILWAY_VOLUME_MOUNT_PATH"
)

PERSISTENT_DATA_DIR = (
    RAILWAY_VOLUME_MOUNT_PATH
    if RAILWAY_VOLUME_MOUNT_PATH
    else os.path.join(
        BASE_DIR,
        "data",
    )
)

AUTH_DB_PATH = os.environ.get(
    "BBUNG_AUTH_DB",
    os.path.join(
        PERSISTENT_DATA_DIR,
        "users.db",
    ),
)

auth_store = AuthStore(
    AUTH_DB_PATH
)

ROOM_TTL_HOURS = float(
    os.environ.get(
        "BBUNG_ROOM_TTL_HOURS",
        "6",
    )
)

ROOM_CLEANUP_INTERVAL_SECONDS = float(
    os.environ.get(
        "BBUNG_ROOM_CLEANUP_INTERVAL_SECONDS",
        "600",
    )
)

room_cleanup_lock = threading.Lock()
room_cleanup_thread = None
room_cleanup_stop_event = threading.Event()
last_room_cleanup_monotonic = 0.0


def _build_game_logger():
    logger = logging.getLogger(
        "bbung.game"
    )

    if logger.handlers:
        return logger

    logger.setLevel(
        logging.INFO
    )

    log_dir = (
        os.path.join(
            PERSISTENT_DATA_DIR,
            "logs",
        )
        if RAILWAY_VOLUME_MOUNT_PATH
        else os.path.join(
            BASE_DIR,
            "logs",
        )
    )

    os.makedirs(
        log_dir,
        exist_ok=True,
    )

    handler = RotatingFileHandler(
        os.path.join(
            log_dir,
            "game_events.log",
        ),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s"
        )
    )

    logger.addHandler(
        handler
    )

    logger.propagate = False

    return logger


game_logger = _build_game_logger()


def log_game_event(
    game=None,
    *,
    action: str,
    actor_id: str | None = None,
    result: str = "OK",
    error: str | None = None,
    extra: dict | None = None,
) -> None:
    """
    실제 서비스에서 게임 흐름을 재현할 수 있도록
    개인정보/손패 전체는 남기지 않고 상태 메타데이터만 기록한다.
    """
    state = (
        game.state
        if game is not None
        else None
    )

    payload = {
        "game_id": (
            game.game_id
            if game is not None
            else None
        ),
        "mode": (
            game.mode.value
            if game is not None
            else None
        ),
        "round": (
            state.round_number
            if state is not None
            else None
        ),
        "status": (
            state.status.value
            if (
                state is not None
                and state.status is not None
            )
            else None
        ),
        "phase": (
            state.turn_phase.value
            if (
                state is not None
                and state.turn_phase is not None
            )
            else None
        ),
        "current_player": (
            state.current_turn_player_id
            if state is not None
            else None
        ),
        "action": action,
        "actor": actor_id,
        "result": result,
    }

    if error is not None:
        payload["error"] = error

    if extra:
        payload["extra"] = extra

    game_logger.info(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def get_bearer_token() -> str | None:
    header = request.headers.get(
        "Authorization",
        "",
    )

    if not header.startswith(
        "Bearer "
    ):
        return None

    token = header[
        len("Bearer "):
    ].strip()

    return token or None


def get_authenticated_user():
    return auth_store.get_user_by_token(
        get_bearer_token()
    )


def touch_game_activity(
    game,
) -> None:
    if game is None:
        return

    game.last_activity_at = datetime.now(
        timezone.utc
    )


def cleanup_stale_online_rooms(
    now: datetime | None = None,
) -> list[str]:
    if now is None:
        now = datetime.now(
            timezone.utc
        )

    cutoff = (
        now
        - timedelta(
            hours=ROOM_TTL_HOURS
        )
    )

    removed = []

    with room_cleanup_lock:
        for game in list(
            manager.get_games_by_mode(
                GameMode.ONLINE
            )
        ):
            if game.last_activity_at <= cutoff:
                cancel_online_bbung_timer(
                    game.game_id
                )

                manager.remove_game(
                    game.game_id
                )

                removed.append(
                    game.game_id
                )

                log_game_event(
                    game,
                    action="ROOM_AUTO_DELETE",
                    actor_id=None,
                    result="OK",
                    extra={
                        "ttl_hours":
                            ROOM_TTL_HOURS,
                    },
                )

    return removed


def maybe_cleanup_stale_online_rooms() -> None:
    global last_room_cleanup_monotonic

    now_mono = time.monotonic()

    if (
        now_mono
        - last_room_cleanup_monotonic
        < ROOM_CLEANUP_INTERVAL_SECONDS
    ):
        return

    last_room_cleanup_monotonic = now_mono

    cleanup_stale_online_rooms()


def start_room_cleanup_thread() -> None:
    global room_cleanup_thread

    if (
        room_cleanup_thread is not None
        and room_cleanup_thread.is_alive()
    ):
        return

    room_cleanup_stop_event.clear()

    def runner():
        while not room_cleanup_stop_event.wait(
            ROOM_CLEANUP_INTERVAL_SECONDS
        ):
            try:
                cleanup_stale_online_rooms()
            except Exception as error:
                game_logger.exception(
                    "room cleanup failed: %s",
                    error,
                )

    room_cleanup_thread = threading.Thread(
        target=runner,
        name="bbung-room-cleanup",
        daemon=True,
    )

    room_cleanup_thread.start()


def is_valid_online_realtime_player(
    game_id: str,
    player_id: str,
) -> bool:
    game = manager.get_game(
        game_id
    )

    if (
        game is None
        or game.mode
        != GameMode.ONLINE
    ):
        return False

    return any(
        player.player_id
        == player_id
        for player in game.state.players
    )


realtime_hub = OnlineRealtimeHub(
    room_player_validator=(
        is_valid_online_realtime_player
    )
)

# 같은 방에 거의 동시에 들어오는 중복 참가 요청도
# 한 명으로 처리하기 위한 서버 측 잠금.
online_join_lock = threading.Lock()

# ONLINE 뻥 반응 타이머.
# 같은 방의 이전 타이머가 늦게 실행되어
# 새 반응 상태를 건드리지 못하도록 세대 번호를 함께 관리한다.
bbung_timer_lock = threading.Lock()
bbung_timers = {}
bbung_timer_generations = {}


def cancel_online_bbung_timer(
    game_id: str,
) -> None:
    """
    해당 방의 예약된 뻥 자동 넘김을 무효화한다.
    이미 실행 직전인 타이머도 generation 검증에서 중단된다.
    """
    with bbung_timer_lock:
        bbung_timer_generations[game_id] = (
            bbung_timer_generations.get(
                game_id,
                0,
            )
            + 1
        )

        timer = bbung_timers.pop(
            game_id,
            None,
        )

        if timer is not None:
            timer.cancel()


def schedule_online_bbung_timeout(
    game,
) -> bool:
    """
    ONLINE의 현재 뻥 반응창을 서버 타이머로 자동 종료한다.

    반응 시간이 끝날 때까지 아무 입력이 없으면:
    REACTION 종료 -> 다음 플레이어 DRAW -> WebSocket 방송.
    """
    if game.mode != GameMode.ONLINE:
        return False

    state = game.state

    if (
        state.status != GameStatus.PLAYING
        or state.turn_phase
        != TurnPhase.REACTION
        or not state.bbung_candidate_player_ids
        or state.bbung_reaction_deadline
        is None
    ):
        cancel_online_bbung_timer(
            game.game_id
        )
        return False

    game_id = game.game_id

    with bbung_timer_lock:
        old_timer = bbung_timers.pop(
            game_id,
            None,
        )

        if old_timer is not None:
            old_timer.cancel()

        generation = (
            bbung_timer_generations.get(
                game_id,
                0,
            )
            + 1
        )

        bbung_timer_generations[
            game_id
        ] = generation

        delay = max(
            0.0,
            (
                state.bbung_reaction_deadline
                - datetime.now(
                    timezone.utc
                )
            ).total_seconds(),
        )

        def on_timeout():
            should_publish = False

            with bbung_timer_lock:
                if (
                    bbung_timer_generations.get(
                        game_id
                    )
                    != generation
                ):
                    return

                bbung_timers.pop(
                    game_id,
                    None,
                )

                current_game = manager.get_game(
                    game_id
                )

                if (
                    current_game is None
                    or current_game.mode
                    != GameMode.ONLINE
                ):
                    return

                current_state = (
                    current_game.state
                )

                if (
                    current_state.status
                    != GameStatus.PLAYING
                    or current_state.turn_phase
                    != TurnPhase.REACTION
                    or not current_state
                        .bbung_candidate_player_ids
                ):
                    return

                engine = GameEngine(
                    current_state
                )

                # 아주 미세하게 일찍 깨어난 경우
                # 남은 시간만큼 다시 예약한다.
                if (
                    engine
                    .is_bbung_reaction_active()
                ):
                    remaining = max(
                        0.001,
                        (
                            current_state
                            .bbung_reaction_deadline
                            - datetime.now(
                                timezone.utc
                            )
                        ).total_seconds(),
                    )

                    retry = threading.Timer(
                        remaining,
                        on_timeout,
                    )
                    retry.daemon = True
                    bbung_timers[
                        game_id
                    ] = retry
                    retry.start()
                    return

                try:
                    engine.close_bbung_reaction_window()
                    engine.advance_turn()

                    log_game_event(
                        current_game,
                        action=(
                            "BBUNG_TIMEOUT_AUTO_PASS"
                        ),
                        actor_id=None,
                        result="OK",
                    )

                    should_publish = True
                except ValueError:
                    return

            if should_publish:
                try:
                    publish_online_state(
                        current_game
                    )
                except Exception:
                    # 타이머의 WebSocket 전송 실패가
                    # 게임 상태 자체를 되돌리지는 않는다.
                    pass

        timer = threading.Timer(
            delay,
            on_timeout,
        )
        timer.daemon = True
        bbung_timers[
            game_id
        ] = timer
        timer.start()

    return True


def serialize_game_for_online_player(
    game,
    viewer_player_id: str,
):
    """
    WebSocket 전송용 온라인 상태.

    본인 손패만 노출하고,
    상대 손패는 hand_count만 유지한다.
    라운드/게임 종료 시에는 기존 규칙대로
    최종 손패를 공개한다.
    """
    data = serialize_game(
        game
    )

    reveal_all_hands = (
        game.state.status
        in (
            GameStatus.ROUND_END,
            GameStatus.GAME_END,
        )
    )

    if reveal_all_hands:
        return data

    for player_data in data[
        "players"
    ]:
        if (
            player_data[
                "player_id"
            ]
            != viewer_player_id
        ):
            player_data[
                "hand"
            ] = []

    return data


def publish_online_state(
    game,
) -> int:
    """
    ONLINE 방의 최신 상태를
    접속 중인 각 플레이어에게 개인화해 전송한다.
    """
    if game.mode != GameMode.ONLINE:
        return 0

    states_by_player_id = {
        player.player_id:
            serialize_game_for_online_player(
                game,
                player.player_id,
            )
        for player in game.state.players
    }

    return realtime_hub.broadcast_states(
        game.game_id,
        states_by_player_id,
    )


def serialize_card(card):
    if card is None:
        return None

    return {
        "card_id": card.card_id,
        "month": card.month,
        "copy_index": card.copy_index,
    }


def serialize_player(player):
    return {
        "player_id": player.player_id,
        "nickname": player.nickname,
        "player_type": player.player_type.value,
        "ai_difficulty": (
            player.ai_difficulty.value
            if player.ai_difficulty is not None
            else None
        ),
        "hand_count": len(player.hand),
        "hand": [
            serialize_card(card)
            for card in player.hand
        ],
        "round_score": player.round_score,
        "total_score": player.total_score,
        "bbung_count": player.bbung_count,
        "bbung_months": list(player.bbung_months),
    }


def serialize_general_bagaji(declaration):
    return {
        "player_id": declaration.player_id,
        "month": declaration.month,
    }


def serialize_bomb_bagaji(declaration):
    return {
        "player_id": declaration.player_id,
        "month": declaration.month,
        "bomb_month": declaration.bomb_month,
    }


def serialize_game(game):
    state = game.state

    return {
        "ok": True,
        "game_id": game.game_id,
        "mode": game.mode.value,
        "owner_id": game.owner_id,
        "max_players": game.max_players,
        "is_private": game.is_private,
        "status": state.status.value,
        "turn_phase": (
            state.turn_phase.value
            if state.turn_phase is not None
            else None
        ),
        "dealer_id": state.dealer_id,
        "dealer_selection_mode": (
            state.dealer_selection_mode
        ),
        "dealer_selection_history": [
            {
                "round": item["round"],
                "winner_ids": list(
                    item["winner_ids"]
                ),
                "draws": {
                    player_id:
                        serialize_card(card)
                    for player_id, card
                    in item["draws"].items()
                },
            }
            for item
            in state.dealer_selection_history
        ],
        "dealer_selection_candidate_ids": list(
            state.dealer_selection_candidate_ids
        ),
        "dealer_selection_current_draws": {
            player_id: serialize_card(card)
            for player_id, card
            in state.dealer_selection_current_draws.items()
        },
        "dealer_selection_round_number": (
            state.dealer_selection_round_number
        ),
        "current_turn_player_id": (
            state.current_turn_player_id
        ),
        "round_number": state.round_number,
        "deck_count": (
            len(state.deck.cards)
            if state.deck is not None
            else 0
        ),
        "discard_pile": [
            serialize_card(card)
            for card in state.discard_pile
        ],
        "last_discarded_card": (
            serialize_card(
                state.last_discarded_card
            )
        ),
        "last_discarded_by_player_id": (
            state.last_discarded_by_player_id
        ),
        "bbung_candidate_player_ids": list(
            state.bbung_candidate_player_ids
        ),
        "bbung_reaction_open": (
            state.turn_phase
            == TurnPhase.REACTION
            and bool(
                state.bbung_candidate_player_ids
            )
        ),
        "players": [
            serialize_player(player)
            for player in state.players
        ],
        "active_bagaji_declarations": [
            serialize_general_bagaji(
                declaration
            )
            for declaration
            in state.active_bagaji_declarations
        ],
        "active_bomb_bagaji_declarations": [
            serialize_bomb_bagaji(
                declaration
            )
            for declaration
            in state.active_bomb_bagaji_declarations
        ],
        "round_end_reason": (
            state.round_end_reason.value
            if state.round_end_reason is not None
            else None
        ),
        "round_winner_id": (
            state.round_winner_id
        ),
        "declared_stop_type": (
            state.declared_stop_type
        ),
        "surprise_stop_dokbak": (
            state.surprise_stop_dokbak
        ),
        "play_phase": (
            2
            if (
                len(state.players) in (5, 6)
                and state.deck_reshuffle_used
            )
            else 1
        ),
        "round_winner_decided_by_tie_break": (
            getattr(
                state,
                "round_winner_decided_by_tie_break",
                False,
            )
        ),
        "game_winner_id": (
            state.game_winner_id
        ),
        "tie_break_player_ids": list(
            state.tie_break_player_ids
        ),
        "tie_break_drawn_cards": {
            player_id: [
                serialize_card(card)
                for card in cards
            ]
            for player_id, cards
            in state.tie_break_drawn_cards.items()
        },
        "tie_break_current_player_id": (
            state.tie_break_player_ids[
                state.tie_break_current_player_index
            ]
            if (
                state.status
                == GameStatus.TIE_BREAK
                and state.tie_break_player_ids
            )
            else None
        ),
        "tie_break_round_number": (
            state.tie_break_round_number
        ),
    }


def get_human_player(state):
    """
    SOLO_AI:
        기존처럼 유일한 HUMAN 플레이어를 반환한다.

    ONLINE:
        요청 헤더 X-Player-ID에 해당하는
        HUMAN 플레이어를 반환한다.
    """
    game = manager.get_game(
        state.game_id
    )

    if (
        game is not None
        and game.mode == GameMode.ONLINE
    ):
        player_id = request.headers.get(
            "X-Player-ID"
        )

        if not player_id:
            return None

        return next(
            (
                player
                for player in state.players
                if (
                    player.player_id
                    == player_id
                    and player.player_type
                    == PlayerType.HUMAN
                )
            ),
            None,
        )

    return next(
        (
            player
            for player in state.players
            if player.player_type
            == PlayerType.HUMAN
        ),
        None,
    )


@app.before_request
def require_login_for_online():
    if request.path.startswith(
        "/api/auth/"
    ):
        return None

    maybe_cleanup_stale_online_rooms()

    needs_auth = request.path.startswith(
        "/api/online/rooms"
    )

    if not needs_auth:
        match = re.match(
            r"^/api/games/([^/]+)",
            request.path,
        )

        if match is not None:
            game = manager.get_game(
                match.group(1)
            )

            needs_auth = (
                game is not None
                and game.mode
                == GameMode.ONLINE
            )

    if not needs_auth:
        return None

    user = get_authenticated_user()

    if user is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "AUTH_REQUIRED",
                    "message": (
                        "온라인 대전은 "
                        "로그인이 필요합니다."
                    ),
                }
            ),
            401,
        )

    request.auth_user = user

    return None


@app.before_request
def require_online_player_identity():
    """
    ONLINE 게임의 공용 /api/games/... 행동 API는
    반드시 해당 방 참가자의 X-Player-ID가 필요하다.
    """
    if request.method != "POST":
        return None

    match = re.match(
        r"^/api/games/([^/]+)/",
        request.path,
    )

    if match is None:
        return None

    game_id = match.group(1)
    game = manager.get_game(
        game_id
    )

    if (
        game is None
        or game.mode
        != GameMode.ONLINE
    ):
        return None

    player_id = request.headers.get(
        "X-Player-ID"
    )

    if not player_id:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "PLAYER_ID_REQUIRED",
                    "message": (
                        "온라인 행동에는 "
                        "플레이어 ID가 필요합니다."
                    ),
                }
            ),
            403,
        )

    if not any(
        player.player_id
        == player_id
        for player in game.state.players
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "PLAYER_NOT_IN_ROOM",
                    "message": (
                        "이 온라인 방의 "
                        "참가자가 아닙니다."
                    ),
                }
            ),
            403,
        )

    return None


@app.after_request
def broadcast_online_mutation(
    response,
):
    """
    성공한 온라인 상태 변경 REST 요청 뒤
    같은 방 WebSocket 접속자들에게
    최신 상태를 전파한다.
    """
    if request.method != "POST":
        return response

    # 실패 응답도 추적하되 응답 본문/손패/닉네임은 기록하지 않는다.
    if response.status_code >= 400:
        match = re.match(
            r"^/api/(?:online/rooms|games)/([^/]+)",
            request.path,
        )

        game = (
            manager.get_game(
                match.group(1)
            )
            if match is not None
            else None
        )

        log_game_event(
            game,
            action=request.path,
            actor_id=(
                request.headers.get(
                    "X-Player-ID"
                )
            ),
            result=(
                f"HTTP_{response.status_code}"
            ),
        )

        return response

    path = request.path

    game_id = None

    match = re.match(
        r"^/api/online/rooms/"
        r"([^/]+)/",
        path,
    )

    if match is None:
        match = re.match(
            r"^/api/games/"
            r"([^/]+)/",
            path,
        )

    if match is not None:
        game_id = match.group(1)

    if game_id is None:
        return response

    game = manager.get_game(
        game_id
    )

    if (
        game is not None
        and response.status_code < 400
    ):
        touch_game_activity(
            game
        )

    if game is not None:
        log_game_event(
            game,
            action=request.path,
            actor_id=(
                request.headers.get(
                    "X-Player-ID"
                )
                or (
                    request.get_json(
                        silent=True
                    ) or {}
                ).get(
                    "owner_id"
                )
            ),
            result="OK",
        )

    if (
        game is not None
        and game.mode
        == GameMode.ONLINE
    ):
        try:
            publish_online_state(
                game
            )
        except Exception as error:
            log_game_event(
                game,
                action="WEBSOCKET_PUBLISH",
                actor_id=None,
                result="ERROR",
                error=str(error),
            )

    return response


@app.errorhandler(Exception)
def handle_unexpected_exception(
    error,
):
    # HTTPException은 Flask의 정상 상태코드 처리를 유지한다.
    from werkzeug.exceptions import HTTPException

    if isinstance(
        error,
        HTTPException,
    ):
        return error

    match = re.match(
        r"^/api/(?:online/rooms|games)/([^/]+)",
        request.path,
    )

    game = (
        manager.get_game(
            match.group(1)
        )
        if match is not None
        else None
    )

    log_game_event(
        game,
        action=request.path,
        actor_id=(
            request.headers.get(
                "X-Player-ID"
            )
        ),
        result="EXCEPTION",
        error=repr(error),
    )

    app.logger.exception(
        "Unhandled exception",
        exc_info=error,
    )

    return (
        jsonify(
            {
                "ok": False,
                "error": "INTERNAL_SERVER_ERROR",
                "message": (
                    "서버 내부 오류가 발생했습니다."
                ),
            }
        ),
        500,
    )


@app.post("/api/auth/register")
def register_user():
    data = request.get_json(
        silent=True
    ) or {}

    try:
        user = auth_store.register(
            username=str(
                data.get(
                    "username",
                    "",
                )
            ),
            password=str(
                data.get(
                    "password",
                    "",
                )
            ),
            nickname=str(
                data.get(
                    "nickname",
                    "",
                )
            ),
        )
    except AuthError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "REGISTER_FAILED",
                    "message": str(error),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "user": user,
        }
    )


@app.post("/api/auth/login")
def login_user():
    data = request.get_json(
        silent=True
    ) or {}

    try:
        result = auth_store.login(
            username=str(
                data.get(
                    "username",
                    "",
                )
            ),
            password=str(
                data.get(
                    "password",
                    "",
                )
            ),
        )
    except AuthError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "LOGIN_FAILED",
                    "message": str(error),
                }
            ),
            401,
        )

    return jsonify(
        {
            "ok": True,
            **result,
        }
    )


@app.get("/api/auth/me")
def get_auth_me():
    user = get_authenticated_user()

    if user is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "AUTH_REQUIRED",
                    "message": (
                        "로그인이 필요합니다."
                    ),
                }
            ),
            401,
        )

    return jsonify(
        {
            "ok": True,
            "user": user,
        }
    )


@app.post("/api/auth/logout")
def logout_user():
    auth_store.logout(
        get_bearer_token()
    )

    return jsonify(
        {
            "ok": True,
        }
    )


@app.get("/events/<game_id>")
def online_state_events(
    game_id: str,
):
    token = request.args.get(
        "token"
    )

    player_id = request.args.get(
        "player_id"
    )

    user = auth_store.get_user_by_token(
        token
    )

    if user is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "AUTH_REQUIRED",
                    "message": (
                        "실시간 연결에 "
                        "로그인이 필요합니다."
                    ),
                }
            ),
            401,
        )

    if (
        not player_id
        or not is_valid_online_realtime_player(
            game_id,
            player_id,
        )
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "ONLINE_PLAYER_NOT_FOUND"
                    ),
                    "message": (
                        "온라인 방 참가자를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            403,
        )

    game = manager.get_game(
        game_id
    )

    touch_game_activity(
        game
    )

    client_queue = (
        realtime_hub.register_client(
            game_id,
            player_id,
        )
    )

    @stream_with_context
    def generate():
        connected_payload = {
            "type": "CONNECTED",
            "game_id": game_id,
            "player_id": player_id,
        }

        yield (
            "data: "
            + json.dumps(
                connected_payload,
                ensure_ascii=False,
            )
            + "\n\n"
        )

        try:
            while True:
                try:
                    payload = (
                        client_queue.get(
                            timeout=25
                        )
                    )

                    yield (
                        "data: "
                        + payload
                        + "\n\n"
                    )

                except queue.Empty:
                    yield ": ping\n\n"

        finally:
            realtime_hub.unregister_client(
                game_id,
                client_queue,
            )

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/")
def index():
    return send_from_directory(
        FRONTEND_DIR,
        "index.html",
    )


@app.get("/css/<path:filename>")
def frontend_css(
    filename: str,
):
    return send_from_directory(
        os.path.join(
            FRONTEND_DIR,
            "css",
        ),
        filename,
    )


@app.get("/js/<path:filename>")
def frontend_js(
    filename: str,
):
    return send_from_directory(
        os.path.join(
            FRONTEND_DIR,
            "js",
        ),
        filename,
    )


@app.get("/assets/<path:filename>")
def frontend_assets(
    filename: str,
):
    return send_from_directory(
        os.path.join(
            FRONTEND_DIR,
            "assets",
        ),
        filename,
    )


@app.get("/api/health")
def health():
    return jsonify(
        {
            "ok": True,
            "message": (
                "Bbung Hwatu backend "
                "is running."
            ),
        }
    )


@app.post("/api/games")
def create_game():
    data = request.get_json(
        silent=True
    ) or {}

    owner_id = data.get(
        "owner_id",
        "LOCAL-USER",
    )

    nickname = data.get(
        "nickname",
        "플레이어",
    )

    ai_difficulty_value = data.get(
        "ai_difficulty",
        AIDifficulty.BEGINNER.value,
    )

    try:
        ai_difficulty = AIDifficulty(
            ai_difficulty_value
        )
    except ValueError:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "INVALID_AI_DIFFICULTY"
                    ),
                    "message": (
                        "지원하지 않는 "
                        "AI 난이도입니다."
                    ),
                }
            ),
            400,
        )

    if ai_difficulty not in (
        AIDifficulty.BEGINNER,
        AIDifficulty.INTERMEDIATE,
        AIDifficulty.ADVANCED,
        AIDifficulty.TAZZA,
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "AI_DIFFICULTY_NOT_READY"
                    ),
                    "message": (
                        "현재는 초보/중수/고수/타짜 AI만 "
                        "사용할 수 있습니다."
                    ),
                }
            ),
            400,
        )

    game_id = (
        f"GAME-"
        f"{len(manager.games) + 1:03d}"
    )

    players = [
        Player(
            player_id=f"{game_id}-P1",
            nickname=nickname,
            player_type=PlayerType.HUMAN,
        ),
        Player(
            player_id=f"{game_id}-P2",
            nickname="AI 1",
            player_type=PlayerType.BOT,
            ai_difficulty=(
                ai_difficulty
            ),
        ),
        Player(
            player_id=f"{game_id}-P3",
            nickname="AI 2",
            player_type=PlayerType.BOT,
            ai_difficulty=(
                ai_difficulty
            ),
        ),
    ]

    state = GameState(
        game_id=game_id,
        players=players,
    )

    game = GameInstance(
        game_id=game_id,
        mode=GameMode.SOLO_AI,
        owner_id=owner_id,
        max_players=3,
        state=state,
    )

    # AI 대전도 온라인과 동일하게 밤일낮짱부터 시작한다.
    # 서버 현재 시각을 한국 표준시(KST)로 변환하여
    # 06:00~17:59 = DAY, 18:00~05:59 = NIGHT 로 자동 결정한다.
    kst = timezone(timedelta(hours=9))
    kst_now = datetime.now(timezone.utc).astimezone(kst)
    dealer_mode = (
        "DAY"
        if 6 <= kst_now.hour < 18
        else "NIGHT"
    )

    state.dealer_selection_mode = dealer_mode
    state.dealer_selection_history = []
    state.dealer_selection_candidate_ids = [
        player.player_id
        for player in state.players
    ]
    state.dealer_selection_current_draws = {}
    state.dealer_selection_round_number = 1
    state.dealer_selection_deck = Deck()
    state.dealer_selection_deck.shuffle()
    state.dealer_id = None
    state.current_turn_player_id = None
    state.turn_phase = None
    state.deck = None
    state.status = GameStatus.DEALER_SELECTION
    state.round_winner_decided_by_tie_break = False

    manager.add_game(game)

    return jsonify(
        serialize_game(game)
    )



@app.post(
    "/api/games/<game_id>/dealer-selection/draw"
)
def draw_solo_dealer_selection_card(
    game_id: str,
):
    try:
        game = manager.require_mode(
            game_id,
            GameMode.SOLO_AI,
        )
    except ValueError as error:
        if str(error) == "GAME_NOT_FOUND":
            return jsonify({
                "ok": False,
                "error": "GAME_NOT_FOUND",
                "message": "AI 대전 게임을 찾을 수 없습니다.",
            }), 404
        return jsonify({
            "ok": False,
            "error": "GAME_MODE_MISMATCH",
            "message": "AI 대전 게임이 아닙니다.",
        }), 400

    state = game.state
    if state.status != GameStatus.DEALER_SELECTION:
        return jsonify({
            "ok": False,
            "error": "DEALER_SELECTION_NOT_ACTIVE",
            "message": "현재 밤일낮짱 진행 중이 아닙니다.",
        }), 400

    human_player = next(
        (
            player
            for player in state.players
            if player.player_type == PlayerType.HUMAN
        ),
        None,
    )
    if human_player is None:
        return jsonify({
            "ok": False,
            "error": "HUMAN_PLAYER_NOT_FOUND",
            "message": "인간 플레이어를 찾을 수 없습니다.",
        }), 400

    human_id = human_player.player_id
    candidates = list(
        state.dealer_selection_candidate_ids
    )

    if human_id not in candidates:
        return jsonify({
            "ok": False,
            "error": "NOT_DEALER_SELECTION_CANDIDATE",
            "message": "이번 추첨 대상이 아닙니다.",
        }), 400

    if human_id in state.dealer_selection_current_draws:
        return jsonify({
            "ok": False,
            "error": "ALREADY_DREW_DEALER_CARD",
            "message": "이번 추첨에서는 이미 카드를 뽑았습니다.",
        }), 400

    if state.dealer_selection_deck is None:
        state.dealer_selection_deck = Deck()
        state.dealer_selection_deck.shuffle()

    human_card = state.dealer_selection_deck.draw()
    state.dealer_selection_current_draws[
        human_id
    ] = human_card

    # 사람이 한 장 뽑으면 같은 추첨 라운드의 AI들은
    # 서버가 즉시 자동으로 한 장씩 뽑는다.
    for candidate_id in candidates:
        if candidate_id == human_id:
            continue
        if candidate_id in state.dealer_selection_current_draws:
            continue
        state.dealer_selection_current_draws[
            candidate_id
        ] = state.dealer_selection_deck.draw()

    while True:
        candidates = list(
            state.dealer_selection_candidate_ids
        )
        draws = dict(
            state.dealer_selection_current_draws
        )

        if not all(
            candidate_id in draws
            for candidate_id in candidates
        ):
            break

        is_night = (
            state.dealer_selection_mode == "NIGHT"
        )
        target_month = (
            min(
                draws[candidate_id].month
                for candidate_id in candidates
            )
            if is_night
            else max(
                draws[candidate_id].month
                for candidate_id in candidates
            )
        )
        winner_ids = [
            candidate_id
            for candidate_id in candidates
            if draws[candidate_id].month
            == target_month
        ]

        state.dealer_selection_history.append({
            "round": state.dealer_selection_round_number,
            "draws": {
                candidate_id: draws[candidate_id]
                for candidate_id in candidates
            },
            "winner_ids": list(winner_ids),
        })

        if len(winner_ids) == 1:
            state.dealer_id = winner_ids[0]
            state.dealer_selection_candidate_ids = []
            state.dealer_selection_current_draws = {}
            state.dealer_selection_deck = None
            break

        state.dealer_selection_candidate_ids = list(
            winner_ids
        )
        state.dealer_selection_current_draws = {}
        state.dealer_selection_round_number += 1
        state.dealer_selection_deck = Deck()
        state.dealer_selection_deck.shuffle()

        # 인간이 동점 후보에 남아 있으면 다음 재추첨은
        # 사람이 다시 버튼을 눌렀을 때 진행한다.
        if human_id in winner_ids:
            break

        # AI끼리만 동점이면 재추첨을 자동으로 끝까지 진행한다.
        for candidate_id in winner_ids:
            state.dealer_selection_current_draws[
                candidate_id
            ] = state.dealer_selection_deck.draw()

    if state.dealer_id is not None:
        dealer_id = state.dealer_id
        state.deck = Deck()
        state.deck.shuffle()
        deal_initial_cards(
            deck=state.deck,
            players=state.players,
            dealer_id=dealer_id,
        )
        state.current_turn_player_id = dealer_id
        state.status = GameStatus.PLAYING
        # 선은 6장을 받고 드로우 없이 바로 1장을 버린다.
        state.turn_phase = TurnPhase.DISCARD

    response_data = serialize_game(game)
    response_data[
        "drawn_dealer_card"
    ] = serialize_card(human_card)
    return jsonify(response_data)


@app.post("/api/online/rooms")
def create_online_room():
    data = request.get_json(
        silent=True
    ) or {}

    auth_user = get_authenticated_user()

    owner_id = (
        f"USER-{auth_user['user_id']}"
        if auth_user is not None
        else data.get(
            "owner_id",
            "LOCAL-USER",
        )
    )

    nickname = data.get(
        "nickname",
        (
            auth_user["nickname"]
            if auth_user is not None
            else "방장"
        ),
    )

    client_id = data.get(
        "client_id"
    )

    try:
        max_players = int(
            data.get(
                "max_players",
                3,
            )
        )
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "INVALID_MAX_PLAYERS",
                    "message": (
                        "인원 수는 3~6 사이의 "
                        "정수여야 합니다."
                    ),
                }
            ),
            400,
        )

    if max_players not in (
        3,
        4,
        5,
        6,
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "INVALID_MAX_PLAYERS",
                    "message": (
                        "온라인 대전은 "
                        "3~6인만 지원합니다."
                    ),
                }
            ),
            400,
        )

    is_private = bool(
        data.get(
            "is_private",
            False,
        )
    )

    room_password = str(
        data.get(
            "room_password",
            "",
        )
        or ""
    ).strip()

    if is_private and len(room_password) < 4:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "ROOM_PASSWORD_TOO_SHORT",
                    "message": (
                        "비밀방 비밀번호는 "
                        "4자 이상이어야 합니다."
                    ),
                }
            ),
            400,
        )

    room_number = (
        len(
            manager.get_games_by_mode(
                GameMode.ONLINE
            )
        )
        + 1
    )

    game_id = (
        f"ROOM-{room_number:03d}"
    )

    while manager.get_game(
        game_id
    ) is not None:
        room_number += 1
        game_id = (
            f"ROOM-{room_number:03d}"
        )

    owner_player = Player(
        player_id=f"{game_id}-P1",
        nickname=nickname,
        player_type=PlayerType.HUMAN,
        client_id=client_id,
    )

    state = GameState(
        game_id=game_id,
        players=[
            owner_player
        ],
    )

    state.status = (
        GameStatus.WAITING
    )

    game = GameInstance(
        game_id=game_id,
        mode=GameMode.ONLINE,
        owner_id=owner_id,
        max_players=max_players,
        is_private=is_private,
        room_password_hash=(
            generate_password_hash(
                room_password
            )
            if is_private
            else None
        ),
        state=state,
    )

    manager.add_game(
        game
    )

    response_data = (
        serialize_game_for_online_player(
            game,
            owner_player.player_id,
        )
    )
    response_data[
        "viewer_player_id"
    ] = owner_player.player_id

    return jsonify(
        response_data
    )


@app.get(
    "/api/online/rooms/<game_id>"
)
def get_online_room(
    game_id: str,
):
    try:
        game = manager.require_mode(
            game_id,
            GameMode.ONLINE,
        )
    except ValueError as error:
        if str(error) == "GAME_NOT_FOUND":
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "GAME_NOT_FOUND",
                        "message": (
                            "온라인 방을 찾을 수 없습니다."
                        ),
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_MODE_MISMATCH",
                    "message": (
                        "온라인 대전 방이 아닙니다."
                    ),
                }
            ),
            400,
        )

    touch_game_activity(
        game
    )

    viewer_player_id = (
        request.args.get(
            "player_id"
        )
    )

    if not viewer_player_id:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "PLAYER_ID_REQUIRED",
                    "message": (
                        "온라인 방 조회에는 "
                        "플레이어 ID가 필요합니다."
                    ),
                }
            ),
            400,
        )

    if not any(
        player.player_id
        == viewer_player_id
        for player in game.state.players
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "PLAYER_NOT_IN_ROOM",
                    "message": (
                        "이 온라인 방의 "
                        "참가자가 아닙니다."
                    ),
                }
            ),
            403,
        )

    response_data = (
        serialize_game_for_online_player(
            game,
            viewer_player_id,
        )
    )
    response_data[
        "viewer_player_id"
    ] = viewer_player_id

    return jsonify(
        response_data
    )


@app.post(
    "/api/online/rooms/<game_id>/join"
)
def join_online_room(
    game_id: str,
):
    try:
        game = manager.require_mode(
            game_id,
            GameMode.ONLINE,
        )
    except ValueError as error:
        if str(error) == "GAME_NOT_FOUND":
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "GAME_NOT_FOUND",
                        "message": (
                            "온라인 방을 찾을 수 없습니다."
                        ),
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_MODE_MISMATCH",
                    "message": (
                        "SOLO_AI 방에는 "
                        "온라인 참가를 할 수 없습니다."
                    ),
                }
            ),
            400,
        )

    state = game.state

    data = request.get_json(
        silent=True
    ) or {}

    auth_user = get_authenticated_user()

    nickname = data.get(
        "nickname",
        (
            auth_user["nickname"]
            if auth_user is not None
            else "플레이어"
        ),
    )

    client_id = data.get(
        "client_id"
    )

    # 중복 클릭/재전송은 같은 참가자로 처리한다.
    # client_id가 이미 있으면 새 Player를 만들지 않는다.
    with online_join_lock:
        if client_id:
            existing_player = next(
                (
                    player
                    for player
                    in state.players
                    if player.client_id
                    == client_id
                ),
                None,
            )

            if existing_player is not None:
                player_id = (
                    existing_player.player_id
                )

                response_data = (
                    serialize_game_for_online_player(
                        game,
                        player_id,
                    )
                )
                response_data[
                    "viewer_player_id"
                ] = player_id
                response_data[
                    "already_joined"
                ] = True

                return jsonify(
                    response_data
                )

        if game.is_private:
            room_password = str(
                data.get(
                    "room_password",
                    "",
                )
                or ""
            )

            if (
                not game.room_password_hash
                or not check_password_hash(
                    game.room_password_hash,
                    room_password,
                )
            ):
                return (
                    jsonify(
                        {
                            "ok": False,
                            "error": "INVALID_ROOM_PASSWORD",
                            "message": (
                                "비밀방 비밀번호가 "
                                "올바르지 않습니다."
                            ),
                        }
                    ),
                    403,
                )

        if (
            state.status
            != GameStatus.WAITING
        ):
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "ROOM_NOT_WAITING",
                        "message": (
                            "이미 시작된 방에는 "
                            "참가할 수 없습니다."
                        ),
                    }
                ),
                400,
            )

        if (
            game.max_players is None
            or len(state.players)
            >= game.max_players
        ):
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "ROOM_FULL",
                        "message": (
                            "방 정원이 가득 찼습니다."
                        ),
                    }
                ),
                400,
            )

        player_id = (
            f"{game_id}-"
            f"P{len(state.players) + 1}"
        )

        state.players.append(
            Player(
                player_id=player_id,
                nickname=nickname,
                player_type=PlayerType.HUMAN,
                client_id=client_id,
            )
        )

    response_data = (
        serialize_game_for_online_player(
            game,
            player_id,
        )
    )
    response_data[
        "viewer_player_id"
    ] = player_id

    return jsonify(
        response_data
    )



@app.post(
    "/api/online/rooms/<game_id>/start"
)
def start_online_room(
    game_id: str,
):
    try:
        game = manager.require_mode(
            game_id,
            GameMode.ONLINE,
        )
    except ValueError as error:
        if str(error) == "GAME_NOT_FOUND":
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "GAME_NOT_FOUND",
                        "message": (
                            "온라인 방을 찾을 수 없습니다."
                        ),
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_MODE_MISMATCH",
                    "message": (
                        "온라인 대전 방이 아닙니다."
                    ),
                }
            ),
            400,
        )

    state = game.state

    if state.status != GameStatus.WAITING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "ROOM_NOT_WAITING",
                    "message": (
                        "이미 시작된 방입니다."
                    ),
                }
            ),
            400,
        )

    # 온라인 게임 자체의 최소 인원은 3명.
    # max_players는 "시작에 필요한 인원"이 아니라
    # 해당 방에 들어올 수 있는 최대 정원으로만 사용한다.
    if len(state.players) < 3:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_ENOUGH_PLAYERS",
                    "message": (
                        "온라인 대전은 최소 3명이 "
                        "모여야 시작할 수 있습니다."
                    ),
                }
            ),
            400,
        )

    data = request.get_json(
        silent=True
    ) or {}

    auth_user = get_authenticated_user()

    owner_id = (
        f"USER-{auth_user['user_id']}"
        if auth_user is not None
        else data.get(
            "owner_id"
        )
    )

    if owner_id != game.owner_id:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "ONLY_OWNER_CAN_START",
                    "message": (
                        "방장만 게임을 "
                        "시작할 수 있습니다."
                    ),
                }
            ),
            403,
        )

    # 밤일낮짱의 낮/밤은 방장이 고르지 않는다.
    # 서버의 현재 시각을 한국 표준시(KST)로 변환해 자동 결정한다.
    # 06:00~17:59 = DAY, 18:00~05:59 = NIGHT
    kst = timezone(timedelta(hours=9))
    kst_now = datetime.now(timezone.utc).astimezone(kst)
    dealer_mode = (
        "DAY"
        if 6 <= kst_now.hour < 18
        else "NIGHT"
    )

    state.dealer_selection_mode = dealer_mode
    state.dealer_selection_history = []
    state.dealer_selection_candidate_ids = [
        player.player_id
        for player in state.players
    ]
    state.dealer_selection_current_draws = {}
    state.dealer_selection_round_number = 1
    state.dealer_selection_deck = Deck()
    state.dealer_selection_deck.shuffle()
    state.dealer_id = None
    state.current_turn_player_id = None
    state.turn_phase = None
    state.deck = None
    state.status = GameStatus.DEALER_SELECTION

    owner_player = next(
        (
            player
            for player in state.players
            if player.player_id
            == f"{game_id}-P1"
        ),
        state.players[0],
    )

    response_data = (
        serialize_game_for_online_player(
            game,
            owner_player.player_id,
        )
    )
    response_data[
        "viewer_player_id"
    ] = owner_player.player_id

    return jsonify(
        response_data
    )


@app.post(
    "/api/online/rooms/<game_id>/dealer-selection/draw"
)
def draw_online_dealer_selection_card(
    game_id: str,
):
    try:
        game = manager.require_mode(
            game_id,
            GameMode.ONLINE,
        )
    except ValueError as error:
        if str(error) == "GAME_NOT_FOUND":
            return jsonify({
                "ok": False,
                "error": "GAME_NOT_FOUND",
                "message": "온라인 방을 찾을 수 없습니다.",
            }), 404
        return jsonify({
            "ok": False,
            "error": "GAME_MODE_MISMATCH",
            "message": "온라인 대전 방이 아닙니다.",
        }), 400

    state = game.state
    if state.status != GameStatus.DEALER_SELECTION:
        return jsonify({
            "ok": False,
            "error": "DEALER_SELECTION_NOT_ACTIVE",
            "message": "현재 밤일낮짱 진행 중이 아닙니다.",
        }), 400

    player_id = request.headers.get("X-Player-ID")
    if not player_id or not any(
        player.player_id == player_id
        for player in state.players
    ):
        return jsonify({
            "ok": False,
            "error": "PLAYER_NOT_IN_ROOM",
            "message": "이 방의 참가자만 카드를 뽑을 수 있습니다.",
        }), 403

    if player_id not in state.dealer_selection_candidate_ids:
        return jsonify({
            "ok": False,
            "error": "NOT_DEALER_SELECTION_CANDIDATE",
            "message": "이번 추첨 대상이 아닙니다.",
        }), 400

    if player_id in state.dealer_selection_current_draws:
        return jsonify({
            "ok": False,
            "error": "ALREADY_DREW_DEALER_CARD",
            "message": "이번 추첨에서는 이미 카드를 뽑았습니다.",
        }), 400

    if state.dealer_selection_deck is None:
        state.dealer_selection_deck = Deck()
        state.dealer_selection_deck.shuffle()

    drawn_card = state.dealer_selection_deck.draw()
    state.dealer_selection_current_draws[player_id] = drawn_card

    candidates = list(state.dealer_selection_candidate_ids)
    round_complete = all(
        candidate_id in state.dealer_selection_current_draws
        for candidate_id in candidates
    )

    if round_complete:
        draws = dict(state.dealer_selection_current_draws)
        is_night = state.dealer_selection_mode == "NIGHT"
        target_month = (
            min(card.month for card in draws.values())
            if is_night
            else max(card.month for card in draws.values())
        )
        winner_ids = [
            candidate_id
            for candidate_id in candidates
            if draws[candidate_id].month == target_month
        ]

        state.dealer_selection_history.append({
            "round": state.dealer_selection_round_number,
            "draws": draws,
            "winner_ids": list(winner_ids),
        })

        if len(winner_ids) == 1:
            state.dealer_id = winner_ids[0]
            state.dealer_selection_candidate_ids = []
            state.dealer_selection_current_draws = {}
            state.dealer_selection_deck = None
        else:
            state.dealer_selection_candidate_ids = list(winner_ids)
            state.dealer_selection_current_draws = {}
            state.dealer_selection_round_number += 1
            state.dealer_selection_deck = Deck()
            state.dealer_selection_deck.shuffle()

    touch_game_activity(game)
    publish_online_state(game)

    response_data = serialize_game_for_online_player(
        game,
        player_id,
    )
    response_data["viewer_player_id"] = player_id
    response_data["drawn_dealer_card"] = serialize_card(drawn_card)
    return jsonify(response_data)


@app.post(
    "/api/online/rooms/<game_id>/confirm-start"
)
def confirm_online_game_start(
    game_id: str,
):
    try:
        game = manager.require_mode(
            game_id,
            GameMode.ONLINE,
        )
    except ValueError as error:
        if str(error) == "GAME_NOT_FOUND":
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "GAME_NOT_FOUND",
                        "message": (
                            "온라인 방을 찾을 수 없습니다."
                        ),
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_MODE_MISMATCH",
                    "message": (
                        "온라인 대전 방이 아닙니다."
                    ),
                }
            ),
            400,
        )

    state = game.state

    if (
        state.status
        != GameStatus.DEALER_SELECTION
        or state.dealer_id is None
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "DEALER_SELECTION_NOT_READY"
                    ),
                    "message": (
                        "밤일낮짱 선 결정이 "
                        "완료되지 않았습니다."
                    ),
                }
            ),
            400,
        )

    data = request.get_json(
        silent=True
    ) or {}

    auth_user = get_authenticated_user()

    owner_id = (
        f"USER-{auth_user['user_id']}"
        if auth_user is not None
        else data.get(
            "owner_id"
        )
    )

    if owner_id != game.owner_id:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "ONLY_OWNER_CAN_START",
                    "message": (
                        "방장만 본게임을 "
                        "시작할 수 있습니다."
                    ),
                }
            ),
            403,
        )

    dealer_id = state.dealer_id
    state.dealer_selection_candidate_ids = []
    state.dealer_selection_current_draws = {}
    state.dealer_selection_deck = None

    # 여기서부터 실제 본게임 48장 덱을 새로 만든다.
    state.deck = Deck()
    state.deck.shuffle()

    for player in state.players:
        player.hand.clear()
        player.round_score = 0
        player.total_score = 0
        player.bbung_count = 0
        player.bbung_months.clear()

    state.discard_pile.clear()
    state.last_discarded_card = None
    state.last_discarded_by_player_id = None
    state.bbung_candidate_player_ids = []
    state.active_bagaji_declarations = []
    state.active_bomb_bagaji_declarations = []

    state.round_number = 1
    state.current_turn_player_id = (
        dealer_id
    )

    deal_initial_cards(
        deck=state.deck,
        players=state.players,
        dealer_id=dealer_id,
    )

    state.status = GameStatus.PLAYING
    state.turn_phase = TurnPhase.DISCARD
    state.round_winner_decided_by_tie_break = (
        False
    )

    owner_player = next(
        (
            player
            for player in state.players
            if player.player_id
            == f"{game_id}-P1"
        ),
        state.players[0],
    )

    response_data = (
        serialize_game_for_online_player(
            game,
            owner_player.player_id,
        )
    )
    response_data[
        "viewer_player_id"
    ] = owner_player.player_id

    return jsonify(
        response_data
    )


@app.get("/api/games/<game_id>")
def get_game(game_id: str):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    return jsonify(
        serialize_game(game)
    )


@app.post(
    "/api/games/<game_id>/discard"
)
def discard_card(game_id: str):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    data = request.get_json(
        silent=True
    ) or {}

    card_id = data.get("card_id")

    if not card_id:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "CARD_ID_REQUIRED",
                    "message": (
                        "버릴 카드 ID가 "
                        "필요합니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    current_player = (
        engine.get_current_player()
    )

    request_player_id = (
        request.headers.get(
            "X-Player-ID"
        )
    )

    if (
        game.mode == GameMode.ONLINE
        and request_player_id
        != current_player.player_id
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_YOUR_TURN",
                    "message": (
                        "현재는 내 차례가 아닙니다."
                    ),
                }
            ),
            403,
        )

    if (
        current_player.player_type
        != PlayerType.HUMAN
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_HUMAN_TURN",
                    "message": (
                        "현재는 사람 플레이어의 "
                        "차례가 아닙니다."
                    ),
                }
            ),
            400,
        )

    try:
        discarded_card = (
            engine.discard_card(
                card_id
            )
        )

        # ONLINE은 AI용 /continue를 호출하지 않는다.
        # 따라서 뻥 후보가 전혀 없는 일반 버림은
        # 여기서 즉시 다음 사람의 DRAW 단계로 넘긴다.
        if (
            game.mode == GameMode.ONLINE
            and state.status
            == GameStatus.PLAYING
            and state.turn_phase
            == TurnPhase.REACTION
        ):
            if state.bbung_candidate_player_ids:
                schedule_online_bbung_timeout(
                    game
                )
            else:
                engine.advance_turn()

    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "INVALID_DISCARD",
                    "message": str(error),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "discarded_card": (
                serialize_card(
                    discarded_card
                )
            ),
            "status": state.status.value,
            "turn_phase": (
                state.turn_phase.value
                if state.turn_phase
                is not None
                else None
            ),
            "current_turn_player_id": (
                state.current_turn_player_id
            ),
            "last_discarded_by_player_id": (
                state.last_discarded_by_player_id
            ),
            "bbung_candidate_player_ids": (
                list(
                    state.bbung_candidate_player_ids
                )
            ),
        }
    )


@app.post(
    "/api/games/<game_id>/draw"
)
def draw_card(game_id: str):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    current_player = (
        engine.get_current_player()
    )

    request_player_id = (
        request.headers.get(
            "X-Player-ID"
        )
    )

    if (
        game.mode == GameMode.ONLINE
        and request_player_id
        != current_player.player_id
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_YOUR_TURN",
                    "message": (
                        "현재는 내 차례가 아닙니다."
                    ),
                }
            ),
            403,
        )

    if (
        current_player.player_type
        != PlayerType.HUMAN
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_HUMAN_TURN",
                    "message": (
                        "현재는 사람 플레이어의 "
                        "차례가 아닙니다."
                    ),
                }
            ),
            400,
        )

    try:
        drawn_card = engine.draw_card()

    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "INVALID_DRAW",
                    "message": str(error),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "drawn_card": (
                serialize_card(
                    drawn_card
                )
                if drawn_card
                is not None
                else None
            ),
            "status": state.status.value,
            "turn_phase": (
                state.turn_phase.value
                if state.turn_phase
                is not None
                else None
            ),
            "current_turn_player_id": (
                state.current_turn_player_id
            ),
            "deck_count": (
                len(state.deck.cards)
                if state.deck
                is not None
                else 0
            ),
            "round_end_reason": (
                state.round_end_reason.value
                if state.round_end_reason
                is not None
                else None
            ),
        }
    )


@app.post(
    "/api/games/<game_id>/next-round"
)
def start_next_round_from_result(
    game_id: str,
):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.ROUND_END:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "ROUND_NOT_ENDED",
                    "message": (
                        "라운드 종료 상태가 아닙니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    try:
        engine.continue_after_round()

        if state.status == GameStatus.PLAYING:
            current_player = (
                engine.get_current_player()
            )

            if (
                current_player.player_type
                == PlayerType.BOT
            ):
                engine.run_beginner_ai_until_human_turn()

    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NEXT_ROUND_FAILED",
                    "message": str(error),
                }
            ),
            400,
        )

    return jsonify(
        serialize_game(game)
    )


@app.post(
    "/api/games/<game_id>/tie-break/draw"
)
def draw_final_tie_break_card(
    game_id: str,
):
    game = manager.get_game(
        game_id
    )

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.TIE_BREAK:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_TIE_BREAK",
                    "message": (
                        "현재는 최종 동점 승부 "
                        "상태가 아닙니다."
                    ),
                }
            ),
            400,
        )

    player_id = (
        request.headers.get(
            "X-Player-ID"
        )
        if game.mode
        == GameMode.ONLINE
        else None
    )

    if game.mode == GameMode.ONLINE:
        if (
            player_id
            not in state.tie_break_player_ids
        ):
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": (
                            "NOT_TIE_BREAK_PLAYER"
                        ),
                        "message": (
                            "최종 동점 승부 "
                            "참가자가 아닙니다."
                        ),
                    }
                ),
                403,
            )

        current_player_id = (
            state.tie_break_player_ids[
                state.tie_break_current_player_index
            ]
        )

        if (
            player_id
            != current_player_id
        ):
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": (
                            "NOT_YOUR_TIE_BREAK_TURN"
                        ),
                        "message": (
                            "현재는 내 3장 승부 "
                            "드로우 차례가 아닙니다."
                        ),
                    }
                ),
                403,
            )

    else:
        # SOLO에서는 현재 타이브레이커 순서의
        # 플레이어를 그대로 사용한다.
        player_id = (
            state.tie_break_player_ids[
                state.tie_break_current_player_index
            ]
        )

    engine = GameEngine(
        state
    )

    try:
        card = (
            engine.draw_tie_break_card(
                player_id
            )
        )
    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "TIE_BREAK_DRAW_FAILED"
                    ),
                    "message": str(
                        error
                    ),
                }
            ),
            400,
        )

    response_data = (
        serialize_game_for_online_player(
            game,
            player_id,
        )
        if game.mode
        == GameMode.ONLINE
        else serialize_game(
            game
        )
    )

    response_data[
        "drawn_tie_break_card"
    ] = serialize_card(
        card
    )

    return jsonify(
        response_data
    )


@app.post(
    "/api/games/<game_id>/continue"
)
def continue_game(game_id: str):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    try:
        if (
            state.turn_phase
            == TurnPhase.REACTION
        ):
            engine.resolve_beginner_ai_reaction_flow()

        if (
            state.status
            != GameStatus.PLAYING
        ):
            response_data = serialize_game(
                game
            )
            response_data["ai_turn_count"] = 0

            return jsonify(
                response_data
            )

        # 사람이 뻥 후보라면
        # 브라우저에서 선택해야 하므로
        # 자동 진행하지 않는다.
        if (
            state.turn_phase
            == TurnPhase.REACTION
        ):
            response_data = serialize_game(
                game
            )
            response_data["ai_turn_count"] = 0

            return jsonify(
                response_data
            )

        ai_turn_count = (
            engine.run_beginner_ai_until_human_turn()
        )

    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "CONTINUE_FAILED",
                    "message": str(error),
                }
            ),
            400,
        )

    current_player = None

    if state.status == GameStatus.PLAYING:
        current_player = (
            engine.get_current_player()
        )

    response_data = serialize_game(
        game
    )

    response_data["ai_turn_count"] = (
        ai_turn_count
    )

    return jsonify(
        response_data
    )


@app.post(
    "/api/games/<game_id>/bbung/pass"
)
def pass_bbung(game_id: str):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    if (
        state.turn_phase
        != TurnPhase.REACTION
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_REACTION_PHASE",
                    "message": (
                        "현재는 뻥 반응 "
                        "단계가 아닙니다."
                    ),
                }
            ),
            400,
        )

    human_player = (
        get_human_player(state)
    )

    if human_player is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "HUMAN_NOT_FOUND",
                    "message": (
                        "사람 플레이어를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            400,
        )

    if (
        human_player.player_id
        not in
        state.bbung_candidate_player_ids
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_BBUNG_CANDIDATE",
                    "message": (
                        "현재 이 플레이어는 "
                        "뻥 후보가 아닙니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    if game.mode == GameMode.ONLINE:
        cancel_online_bbung_timer(
            game_id
        )

    try:
        # 사용자가 명시적으로
        # 뻥을 포기했으므로 반응창 종료.
        engine.close_bbung_reaction_window()

        # 현재 버린 사람 다음 순서로 이동.
        engine.advance_turn()

        # 다음이 AI라면 사람 차례 또는
        # 사람 반응 시점까지 자동 진행.
        ai_turn_count = (
            engine.run_beginner_ai_until_human_turn()
        )

    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "BBUNG_PASS_FAILED",
                    "message": str(error),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "status": state.status.value,
            "turn_phase": (
                state.turn_phase.value
                if state.turn_phase
                is not None
                else None
            ),
            "current_turn_player_id": (
                state.current_turn_player_id
            ),
            "ai_turn_count": ai_turn_count,
            "bbung_candidate_player_ids": (
                list(
                    state.bbung_candidate_player_ids
                )
            ),
        }
    )


@app.post(
    "/api/games/<game_id>/bbung"
)
def declare_human_bbung(
    game_id: str,
):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    data = request.get_json(
        silent=True
    ) or {}

    matching_card_ids = (
        data.get(
            "matching_card_ids"
        )
    )

    extra_discard_card_id = (
        data.get(
            "extra_discard_card_id"
        )
    )

    if (
        not isinstance(
            matching_card_ids,
            list,
        )
        or len(
            matching_card_ids
        ) != 2
        or not extra_discard_card_id
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "INVALID_BBUNG_REQUEST",
                    "message": (
                        "뻥 카드 2장과 "
                        "추가 버림 카드 1장이 "
                        "필요합니다."
                    ),
                }
            ),
            400,
        )

    human_player = (
        get_human_player(state)
    )

    if human_player is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "HUMAN_NOT_FOUND",
                    "message": (
                        "사람 플레이어를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            400,
        )

    if (
        human_player.player_id
        not in
        state.bbung_candidate_player_ids
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_BBUNG_CANDIDATE",
                    "message": (
                        "현재 이 플레이어는 "
                        "뻥 후보가 아닙니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    if game.mode == GameMode.ONLINE:
        cancel_online_bbung_timer(
            game_id
        )

    try:
        discarded_cards = (
            engine.declare_bbung(
                player_id=(
                    human_player.player_id
                ),
                matching_card_ids=(
                    matching_card_ids
                ),
                extra_discard_card_id=(
                    extra_discard_card_id
                ),
            )
        )

        # 사람이 추가로 버린 카드에 대해
        # AI의 연속 뻥을 처리한다.
        engine.resolve_beginner_ai_reaction_flow()

        # AI 반응이 끝나고 일반 턴으로
        # 넘어간 경우에만 AI 자동 진행.
        if (
            state.status
            == GameStatus.PLAYING
            and state.turn_phase
            != TurnPhase.REACTION
        ):
            engine.run_beginner_ai_until_human_turn()

        if (
            game.mode == GameMode.ONLINE
            and state.status
            == GameStatus.PLAYING
            and state.turn_phase
            == TurnPhase.REACTION
            and state.bbung_candidate_player_ids
        ):
            schedule_online_bbung_timeout(
                game
            )

    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "BBUNG_FAILED",
                    "message": str(error),
                }
            ),
            400,
        )

    discarded = []

    for card in discarded_cards:
        discarded.append(
            serialize_card(card)
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "discarded_cards": (
                discarded
            ),
            "status": state.status.value,
            "turn_phase": (
                state.turn_phase.value
                if state.turn_phase
                is not None
                else None
            ),
            "current_turn_player_id": (
                state.current_turn_player_id
            ),
            "bbung_candidate_player_ids": (
                list(
                    state.bbung_candidate_player_ids
                )
            ),
        }
    )



@app.post(
    "/api/games/<game_id>/bagaji/bomb"
)
def declare_human_bomb_bagaji(
    game_id: str,
):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    human_player = (
        get_human_player(state)
    )

    if human_player is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "HUMAN_NOT_FOUND",
                    "message": (
                        "사람 플레이어를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            400,
        )

    # 폭탄 바가지는 손패 5장이
    # 정확히 3장 같은 월 + 2장 다른 같은 월이어야 한다.
    # 2장 쪽 월이 바가지 대상 월이다.
    month_counts = {}

    for card in human_player.hand:
        month_counts[card.month] = (
            month_counts.get(
                card.month,
                0,
            )
            + 1
        )

    target_month = next(
        (
            month
            for month, count
            in month_counts.items()
            if count == 2
        ),
        None,
    )

    engine = GameEngine(state)

    try:
        if (
            len(human_player.hand) != 5
            or sorted(
                month_counts.values()
            )
            != [2, 3]
            or target_month is None
        ):
            raise ValueError(
                "폭탄 바가지 조건이 아닙니다."
            )

        declaration = (
            engine.declare_bomb_bagaji(
                player_id=(
                    human_player.player_id
                ),
                month=target_month,
            )
        )

    except ValueError:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "BOMB_BAGAJI_FAILED"
                    ),
                    "message": (
                        "현재 폭탄 바가지를 "
                        "선언할 수 없습니다."
                    ),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "declaration": (
                serialize_bomb_bagaji(
                    declaration
                )
            ),
            "active_bomb_bagaji_declarations": [
                serialize_bomb_bagaji(
                    item
                )
                for item
                in state
                    .active_bomb_bagaji_declarations
            ],
        }
    )


@app.post(
    "/api/games/<game_id>/bagaji/bomb/cancel"
)
def cancel_human_bomb_bagaji(
    game_id: str,
):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    human_player = (
        get_human_player(state)
    )

    if human_player is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "HUMAN_NOT_FOUND",
                    "message": (
                        "사람 플레이어를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    try:
        declaration = (
            engine.cancel_bomb_bagaji(
                human_player.player_id
            )
        )

    except ValueError:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "BOMB_BAGAJI_CANCEL_FAILED"
                    ),
                    "message": (
                        "철회할 폭탄 바가지가 "
                        "없습니다."
                    ),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "cancelled_declaration": (
                serialize_bomb_bagaji(
                    declaration
                )
            ),
        }
    )


@app.post(
    "/api/games/<game_id>/bagaji/general"
)
def declare_human_general_bagaji(
    game_id: str,
):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    human_player = (
        get_human_player(state)
    )

    if human_player is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "HUMAN_NOT_FOUND",
                    "message": (
                        "사람 플레이어를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            400,
        )

    # 일반 바가지는 손패가 정확히 2장이고
    # 두 장이 같은 월이어야 하므로,
    # 사용자가 월을 고르지 않고 서버가 현재 손패에서 결정한다.
    month = (
        human_player.hand[0].month
        if len(human_player.hand) == 2
        else None
    )

    engine = GameEngine(state)

    try:
        if month is None:
            raise ValueError(
                "일반 바가지 조건이 아닙니다."
            )

        declaration = (
            engine.declare_general_bagaji(
                player_id=(
                    human_player.player_id
                ),
                month=month,
            )
        )

    except ValueError:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "GENERAL_BAGAJI_FAILED"
                    ),
                    "message": (
                        "현재 일반 바가지를 "
                        "선언할 수 없습니다."
                    ),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "declaration": (
                serialize_general_bagaji(
                    declaration
                )
            ),
            "active_bagaji_declarations": [
                serialize_general_bagaji(
                    item
                )
                for item
                in state
                    .active_bagaji_declarations
            ],
        }
    )


@app.post(
    "/api/games/<game_id>/bagaji/general/cancel"
)
def cancel_human_general_bagaji(
    game_id: str,
):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    human_player = (
        get_human_player(state)
    )

    if human_player is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "HUMAN_NOT_FOUND",
                    "message": (
                        "사람 플레이어를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    try:
        declaration = (
            engine.cancel_general_bagaji(
                human_player.player_id
            )
        )

    except ValueError:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "GENERAL_BAGAJI_CANCEL_FAILED"
                    ),
                    "message": (
                        "철회할 일반 바가지가 "
                        "없습니다."
                    ),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "cancelled_declaration": (
                serialize_general_bagaji(
                    declaration
                )
            ),
        }
    )


@app.post(
    "/api/games/<game_id>/surprise-stop"
)
def declare_human_surprise_stop(
    game_id: str,
):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    human_player = (
        get_human_player(state)
    )

    if human_player is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "HUMAN_NOT_FOUND",
                    "message": (
                        "사람 플레이어를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            400,
        )

    if (
        state.current_turn_player_id
        != human_player.player_id
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_HUMAN_TURN",
                    "message": (
                        "현재는 사람 플레이어의 "
                        "차례가 아닙니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    try:
        score = (
            engine.declare_surprise_stop(
                human_player.player_id
            )
        )

    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "SURPRISE_STOP_FAILED"
                    ),
                    "message": str(error),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "score": score,
            "surprise_stop_dokbak": (
                state.surprise_stop_dokbak
            ),
            "status": state.status.value,
            "turn_phase": (
                state.turn_phase.value
                if state.turn_phase
                is not None
                else None
            ),
            "round_end_reason": (
                state.round_end_reason.value
                if state.round_end_reason
                is not None
                else None
            ),
            "round_winner_id": (
                state.round_winner_id
            ),
            "players": [
                {
                    "player_id": (
                        player.player_id
                    ),
                    "nickname": (
                        player.nickname
                    ),
                    "round_score": (
                        player.round_score
                    ),
                    "total_score": (
                        player.total_score
                    ),
                }
                for player in state.players
            ],
        }
    )


@app.post(
    "/api/games/<game_id>/stop"
)
def declare_human_stop(
    game_id: str,
):
    game = manager.get_game(game_id)

    if game is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_FOUND",
                    "message": (
                        "게임을 찾을 수 없습니다."
                    ),
                }
            ),
            404,
        )

    state = game.state

    if state.status != GameStatus.PLAYING:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "GAME_NOT_PLAYING",
                    "message": (
                        "현재 진행 중인 "
                        "라운드가 아닙니다."
                    ),
                }
            ),
            400,
        )

    human_player = (
        get_human_player(state)
    )

    if human_player is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "HUMAN_NOT_FOUND",
                    "message": (
                        "사람 플레이어를 "
                        "찾을 수 없습니다."
                    ),
                }
            ),
            400,
        )

    if (
        state.current_turn_player_id
        != human_player.player_id
    ):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "NOT_HUMAN_TURN",
                    "message": (
                        "현재는 사람 플레이어의 "
                        "차례가 아닙니다."
                    ),
                }
            ),
            400,
        )

    data = request.get_json(
        silent=True
    ) or {}

    requested_stop_type = (
        data.get("stop_type")
    )

    if not requested_stop_type:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "STOP_TYPE_REQUIRED",
                    "message": (
                        "선언할 STOP 종류가 "
                        "필요합니다."
                    ),
                }
            ),
            400,
        )

    engine = GameEngine(state)

    available_stops = (
        engine.get_current_player_stops()
    )

    selected_stop = next(
        (
            stop_type
            for stop_type
            in available_stops
            if stop_type.value
            == requested_stop_type
        ),
        None,
    )

    if selected_stop is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "INVALID_STOP",
                    "message": (
                        "현재 손패로 선언할 수 "
                        "없는 STOP입니다."
                    ),
                }
            ),
            400,
        )

    try:
        score = engine.declare_stop(
            selected_stop
        )

    except ValueError as error:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "STOP_FAILED",
                    "message": str(error),
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "game_id": game_id,
            "declared_stop_type": (
                selected_stop.value
            ),
            "score": score,
            "status": state.status.value,
            "turn_phase": (
                state.turn_phase.value
                if state.turn_phase
                is not None
                else None
            ),
            "round_end_reason": (
                state.round_end_reason.value
                if state.round_end_reason
                is not None
                else None
            ),
            "round_winner_id": (
                state.round_winner_id
            ),
            "players": [
                {
                    "player_id": (
                        player.player_id
                    ),
                    "nickname": (
                        player.nickname
                    ),
                    "round_score": (
                        player.round_score
                    ),
                    "total_score": (
                        player.total_score
                    ),
                }
                for player
                in state.players
            ],
        }
    )


# Gunicorn으로 import되어 실행될 때도
# 오래된 방 정리 스레드가 시작되어야 한다.
start_room_cleanup_thread()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                "5001",
            )
        ),
        debug=False,
        threaded=True,
        use_reloader=False,
    )
