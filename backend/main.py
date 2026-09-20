import time

from game.deck import Deck
from game.engine import GameEngine
from game.instance import GameInstance, GameMode
from game.manager import GameManager
from game.models import (
    AIDifficulty,
    Card,
    Player,
    PlayerType,
)

from game.rules.bagaji import (
    can_declare_bomb_bagaji,
    get_bomb_bagaji_months,
)

from game.rules.bbung import (
    can_declare_bbung,
    get_bbung_cards,
)

from game.rules.bomb import (
    calculate_hand_score,
    get_bomb_months,
)

from game.rules.stop import (
    StopType,
    calculate_stop_score,
    get_available_stops,
)

from game.setup import deal_initial_cards
from game.state import (
    GameState,
    GameStatus,
    RoundEndReason,
    TurnPhase,
)

from game.integrity import (
    GameCardIntegrityError,
    validate_game_card_integrity,
)
from game.rules.surprise_stop import (
    can_declare_surprise_stop,
    calculate_two_card_sum,
    count_bbung_players,
)

from game.ai.beginner import (
    choose_beginner_discard,
)





def make_test_cards(months: list[int]) -> list[Card]:
    """
    테스트용 월 목록을 실제 카드 규칙에 맞는 Card 목록으로 변환한다.

    같은 월 카드는 copy_index 1~4를 순서대로 사용한다.
    """
    month_copy_counts = {}
    cards = []

    for month in months:
        copy_index = month_copy_counts.get(month, 0) + 1

        if copy_index > 4:
            raise ValueError(
                f"{month}월 카드는 4장을 초과할 수 없습니다."
            )

        month_copy_counts[month] = copy_index

        cards.append(
            Card(
                month=month,
                copy_index=copy_index,
            )
        )

    return cards


def create_test_game(
    game_id: str,
    owner_id: str,
    human_nickname: str,
) -> GameInstance:
    """
    테스트용 3인 AI 게임방 하나를 생성한다.
    """

    players = [
        Player(
            player_id=f"{game_id}-P1",
            nickname=human_nickname,
            player_type=PlayerType.HUMAN,
        ),
        Player(
            player_id=f"{game_id}-P2",
            nickname="AI 1",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.BEGINNER,
        ),
        Player(
            player_id=f"{game_id}-P3",
            nickname="AI 2",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.BEGINNER,
        ),
    ]

    game_state = GameState(
        game_id=game_id,
        players=players,
    )

    game = GameInstance(
        game_id=game_id,
        mode=GameMode.SOLO_AI,
        owner_id=owner_id,
        state=game_state,
    )

    dealer_id = players[0].player_id

    game.state.dealer_id = dealer_id
    game.state.current_turn_player_id = dealer_id

    # 선은 6장을 받은 상태에서
    # 드로우 없이 바로 버리기부터 시작한다.
    game.state.turn_phase = TurnPhase.DISCARD

    game.state.deck = Deck()
    game.state.deck.shuffle()

    deal_initial_cards(
        deck=game.state.deck,
        players=game.state.players,
        dealer_id=dealer_id,
    )

    game.state.status = GameStatus.PLAYING

    return game


def main() -> None:
    # ============================================================
    # 1. GameManager 독립성 테스트
    # ============================================================

    manager = GameManager()

    game1 = create_test_game(
        game_id="GAME-001",
        owner_id="USER-001",
        human_nickname="플레이어 1",
    )

    game2 = create_test_game(
        game_id="GAME-002",
        owner_id="USER-002",
        human_nickname="테스트 유저",
    )

    manager.add_game(game1)
    manager.add_game(game2)

    print("=== GameManager 독립성 테스트 ===")
    print(f"등록된 게임 수: {len(manager.games)}")

    print()

    loaded_game1 = manager.get_game("GAME-001")

    if loaded_game1 is not None:
        print(f"[{loaded_game1.game_id}]")
        print(f"소유자: {loaded_game1.owner_id}")
        print(f"덱 ID: {loaded_game1.state.deck_id}")
        print("플레이어별 카드 수:")

        for player in loaded_game1.state.players:
            print(
                f"  {player.nickname}: "
                f"{len(player.hand)}장"
            )

        print(
            f"남은 덱: "
            f"{len(loaded_game1.state.deck.cards)}장"
        )

    print()

    loaded_game2 = manager.get_game("GAME-002")

    if loaded_game2 is not None:
        print(f"[{loaded_game2.game_id}]")
        print(f"소유자: {loaded_game2.owner_id}")
        print(f"덱 ID: {loaded_game2.state.deck_id}")
        print("플레이어별 카드 수:")

        for player in loaded_game2.state.players:
            print(
                f"  {player.nickname}: "
                f"{len(player.hand)}장"
            )

        print(
            f"남은 덱: "
            f"{len(loaded_game2.state.deck.cards)}장"
        )

    print()

    print("=== 객체 공유 검사 ===")

    print(
        "GameState 공유:",
        game1.state is game2.state,
    )

    print(
        "Deck 공유:",
        game1.state.deck is game2.state.deck,
    )

    print(
        "Players 리스트 공유:",
        game1.state.players is game2.state.players,
    )

    print(
        "P1 Hand 공유:",
        game1.state.players[0].hand
        is game2.state.players[0].hand,
    )

    # ============================================================
    # 2. 실제 턴 흐름 테스트
    # ============================================================

    print()
    print("=== 실제 턴 흐름 테스트 ===")

    engine = GameEngine(game1.state)

    dealer = engine.get_current_player()

    print(
        f"선 첫 행동 전: {dealer.nickname} / "
        f"{len(dealer.hand)}장 / "
        f"{game1.state.turn_phase}"
    )

    dealer_discard_card_id = dealer.hand[0].card_id

    engine.discard_card(
        dealer_discard_card_id
    )

    print(
        f"마지막 버림 카드: "
        f"{game1.state.last_discarded_card.card_id}"
    )

    print(
        f"마지막 버린 플레이어: "
        f"{game1.state.last_discarded_by_player_id}"
    )

    print(
        f"선 버리기 후: {dealer.nickname} / "
        f"{len(dealer.hand)}장"
    )

    # 랜덤 패에서 뻥 후보가 생겼을 수도 있으므로
    # 테스트 진행을 위해 반응창을 닫는다.
    if game1.state.bbung_reaction_open:
        engine.close_bbung_reaction_window()

    engine.advance_turn()

    second_player = engine.get_current_player()

    print(
        f"다음 턴: {second_player.nickname} / "
        f"{len(second_player.hand)}장 / "
        f"{game1.state.turn_phase}"
    )

    drawn_card = engine.draw_card()

    print(
        f"드로우 후: {second_player.nickname} / "
        f"{len(second_player.hand)}장 / "
        f"{game1.state.turn_phase}"
    )

    engine.discard_card(
        drawn_card.card_id
    )

    print(
        f"버리기 후: {second_player.nickname} / "
        f"{len(second_player.hand)}장"
    )

    if game1.state.bbung_reaction_open:
        engine.close_bbung_reaction_window()

    engine.advance_turn()

    third_player = engine.get_current_player()

    print(
        f"다음 턴: {third_player.nickname} / "
        f"{len(third_player.hand)}장 / "
        f"{game1.state.turn_phase}"
    )

    total_cards = (
        len(game1.state.deck.cards)
        + len(game1.state.discard_pile)
        + sum(
            len(player.hand)
            for player in game1.state.players
        )
    )

    print(
        f"버림패: "
        f"{len(game1.state.discard_pile)}장"
    )

    print(
        f"남은 덱: "
        f"{len(game1.state.deck.cards)}장"
    )

    print(
        f"전체 카드 수: "
        f"{total_cards}장"
    )

    # ============================================================
    # 3. 불법 턴 행동 차단 테스트
    # ============================================================

    print()
    print("=== 불법 행동 차단 테스트 ===")

    test_game = create_test_game(
        game_id="TEST-ILLEGAL",
        owner_id="TEST-USER",
        human_nickname="테스트 플레이어",
    )

    test_engine = GameEngine(
        test_game.state
    )

    try:
        test_engine.draw_card()
        print("❌ 선 첫 턴 드로우 차단 실패")
    except ValueError:
        print("✅ 선 첫 턴 드로우 차단 성공")

    try:
        test_engine.advance_turn()
        print("❌ 버리기 전 턴 넘기기 차단 실패")
    except ValueError:
        print("✅ 버리기 전 턴 넘기기 차단 성공")

    dealer = test_engine.get_current_player()

    first_discard_id = (
        dealer.hand[0].card_id
    )

    test_engine.discard_card(
        first_discard_id
    )

    second_discard_id = (
        dealer.hand[0].card_id
    )

    try:
        test_engine.discard_card(
            second_discard_id
        )
        print("❌ 연속 버리기 차단 실패")
    except ValueError:
        print("✅ 연속 버리기 차단 성공")

    # 이 테스트에서는 뻥 반응 자체가 목적이 아니므로
    # 후보가 있으면 강제로 닫고 다음 턴으로 간다.
    if test_game.state.bbung_reaction_open:
        test_engine.close_bbung_reaction_window()

    test_engine.advance_turn()

    second_player = (
        test_engine.get_current_player()
    )

    test_engine.draw_card()

    try:
        test_engine.draw_card()
        print("❌ 연속 드로우 차단 실패")
    except ValueError:
        print("✅ 연속 드로우 차단 성공")

    try:
        test_engine.advance_turn()
        print(
            "❌ 드로우 후 버리기 전 "
            "턴 넘기기 차단 실패"
        )
    except ValueError:
        print(
            "✅ 드로우 후 버리기 전 "
            "턴 넘기기 차단 성공"
        )

    print(
        f"현재 플레이어: "
        f"{second_player.nickname} / "
        f"{len(second_player.hand)}장 / "
        f"{test_game.state.turn_phase}"
    )

    # ============================================================
    # 4. STOP 판정 테스트
    # ============================================================

    print()
    print("=== STOP 판정 테스트 ===")

    stop_test_hands = {
        "스트레이트": [
            1, 2, 3, 4, 5, 6
        ],
        "고득점": [
            8, 9, 10, 10, 11, 12
        ],
        "또이또이": [
            2, 2, 5, 5, 9, 9
        ],
        "-100 (4장+2장)": [
            3, 3, 3, 3, 7, 7
        ],
        "-100 (합계 10 이하)": [
            1, 1, 1, 2, 2, 2
        ],
        "-200": [
            1, 1, 1, 1, 2, 2
        ],
        "STOP 없음": [
            1, 2, 4, 7, 8, 11
        ],
    }

    for test_name, months in stop_test_hands.items():
        cards = make_test_cards(
            months
        )

        available_stops = (
            get_available_stops(cards)
        )

        stop_names = [
            stop_type.value
            for stop_type in available_stops
        ]

        print(
            f"{test_name}: "
            f"{months} -> "
            f"{stop_names}"
        )

    # ============================================================
    # 5. STOP 점수 계산 테스트
    # ============================================================

    print()
    print("=== STOP 점수 계산 테스트 ===")

    stop_score_tests = [
        (
            "스트레이트",
            [1, 2, 3, 4, 5, 6],
            StopType.STRAIGHT,
            -21,
        ),
        (
            "고득점",
            [8, 9, 10, 10, 11, 12],
            StopType.HIGH_SUM,
            -60,
        ),
        (
            "또이또이",
            [2, 2, 5, 5, 9, 9],
            StopType.TTOI_TTOI,
            0,
        ),
        (
            "-100",
            [3, 3, 3, 3, 7, 7],
            StopType.MINUS_100,
            -100,
        ),
        (
            "-200",
            [1, 1, 1, 1, 2, 2],
            StopType.MINUS_200,
            -200,
        ),
    ]

    for (
        test_name,
        months,
        selected_stop,
        expected_score,
    ) in stop_score_tests:
        cards = make_test_cards(
            months
        )

        score = calculate_stop_score(
            cards,
            selected_stop,
        )

        passed = (
            score == expected_score
        )

        print(
            f"{test_name}: "
            f"{months} -> "
            f"{score}점 / "
            f"예상 {expected_score}점 / "
            f"{'✅ 성공' if passed else '❌ 실패'}"
        )

    # ============================================================
    # 6. 복수 STOP 테스트
    # ============================================================

    print()
    print("=== 복수 STOP 선택지 테스트 ===")

    multiple_stop_tests = [
        (
            "고득점 + 또이또이",
            [10, 10, 11, 11, 12, 12],
            [
                StopType.HIGH_SUM,
                StopType.TTOI_TTOI,
            ],
        ),
        (
            "고득점 + -100",
            [12, 12, 12, 12, 11, 11],
            [
                StopType.HIGH_SUM,
                StopType.MINUS_100,
            ],
        ),
    ]

    for (
        test_name,
        months,
        expected_stops,
    ) in multiple_stop_tests:
        cards = make_test_cards(
            months
        )

        available_stops = (
            get_available_stops(cards)
        )

        passed = (
            available_stops
            == expected_stops
        )

        actual_names = [
            stop_type.value
            for stop_type in available_stops
        ]

        expected_names = [
            stop_type.value
            for stop_type in expected_stops
        ]

        print(
            f"{test_name}: "
            f"{months} -> "
            f"{actual_names} / "
            f"예상 {expected_names} / "
            f"{'✅ 성공' if passed else '❌ 실패'}"
        )

    # ============================================================
    # 7. GameEngine STOP 조회 테스트
    # ============================================================

    print()
    print("=== GameEngine STOP 조회 테스트 ===")

    stop_game = create_test_game(
        game_id="TEST-STOP-ENGINE",
        owner_id="TEST-USER",
        human_nickname="STOP 테스트",
    )

    stop_engine = GameEngine(
        stop_game.state
    )

    stop_player = (
        stop_engine.get_current_player()
    )

    stop_player.hand = make_test_cards(
        [10, 10, 11, 11, 12, 12]
    )

    available_stops = (
        stop_engine.get_current_player_stops()
    )

    stop_names = [
        stop_type.value
        for stop_type in available_stops
    ]

    print(
        f"현재 단계: "
        f"{stop_game.state.turn_phase}"
    )

    stop_player_months = [
        card.month
        for card in stop_player.hand
    ]

    print(
        f"현재 손패: "
        f"{stop_player_months}"
    )

    print(
        f"선언 가능한 STOP: "
        f"{stop_names}"
    )

    # ============================================================
    # 8. GameEngine STOP 선언 + 일반 정산 테스트
    # ============================================================

    print()
    print("=== GameEngine STOP 선언 테스트 ===")

    declare_stop_game = create_test_game(
        game_id="TEST-DECLARE-STOP",
        owner_id="TEST-USER",
        human_nickname="STOP 선언 테스트",
    )

    declare_stop_engine = GameEngine(
        declare_stop_game.state
    )

    declare_stop_player = (
        declare_stop_engine.get_current_player()
    )

    declare_stop_player.hand = make_test_cards(
        [10, 10, 11, 11, 12, 12]
    )

    # 폭탄 3장은 0점,
    # 남은 3 + 7 = 10점
    declare_stop_game.state.players[1].hand = (
        make_test_cards(
            [3, 3, 3, 3, 7]
        )
    )

    declare_stop_game.state.players[2].hand = (
        make_test_cards(
            [6, 7, 8, 9, 10]
        )
    )

    stop_score = (
        declare_stop_engine.declare_stop(
            StopType.HIGH_SUM
        )
    )

    print(
        f"선택한 STOP: "
        f"{StopType.HIGH_SUM.value}"
    )

    print(
        f"STOP 점수: "
        f"{stop_score}"
    )

    print(
        f"플레이어 round_score: "
        f"{declare_stop_player.round_score}"
    )

    print(
        f"게임 상태: "
        f"{declare_stop_game.state.status}"
    )

    print(
        f"턴 단계: "
        f"{declare_stop_game.state.turn_phase}"
    )

    print(
        f"라운드 승자 ID: "
        f"{declare_stop_game.state.round_winner_id}"
    )

    print(
        f"라운드 종료 이유: "
        f"{declare_stop_game.state.round_end_reason}"
    )

    print(
        f"선언된 STOP: "
        f"{declare_stop_game.state.declared_stop_type}"
    )

    print("플레이어별 라운드 점수:")

    for player in declare_stop_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )

    print("플레이어별 누적 점수:")

    for player in declare_stop_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.total_score}점"
        )

    try:
        declare_stop_engine.finalize_round(
            winner_id=declare_stop_player.player_id,
            reason=RoundEndReason.NORMAL_STOP,
        )

        print("❌ 중복 라운드 정산 차단 실패")

    except ValueError:
        print("✅ 중복 라운드 정산 차단 성공")

    # ============================================================
    # 9. 폭탄 판정/점수 테스트
    # ============================================================

    print()
    print("=== 폭탄 판정 및 손패 점수 테스트 ===")

    bomb_tests = [
        (
            "폭탄 1개",
            [3, 3, 3, 5, 2],
            [3],
            7,
        ),
        (
            "폭탄 없음",
            [1, 2, 3, 4, 5],
            [],
            15,
        ),
        (
            "4장 중 3장은 폭탄",
            [3, 3, 3, 3, 5, 2],
            [3],
            10,
        ),
        (
            "4장 폭탄 + 일반 카드",
            [3, 3, 3, 3, 7],
            [3],
            10,
        ),
        (
            "폭탄 2개",
            [2, 2, 2, 7, 7, 7],
            [2, 7],
            0,
        ),
    ]

    for (
        test_name,
        months,
        expected_bomb_months,
        expected_score,
    ) in bomb_tests:
        cards = make_test_cards(
            months
        )

        bomb_months = (
            get_bomb_months(cards)
        )

        score = (
            calculate_hand_score(cards)
        )

        bomb_passed = (
            bomb_months
            == expected_bomb_months
        )

        score_passed = (
            score
            == expected_score
        )

        print(
            f"{test_name}: "
            f"{months} -> "
            f"폭탄 {bomb_months} / "
            f"예상 {expected_bomb_months} / "
            f"{'✅' if bomb_passed else '❌'}"
        )

        print(
            f"  손패 점수: "
            f"{score}점 / "
            f"예상 {expected_score}점 / "
            f"{'✅ 성공' if score_passed else '❌ 실패'}"
        )

    # ============================================================
    # 10. 순수 뻥 판정 테스트
    # ============================================================

    print()
    print("=== 뻥 판정 테스트 ===")

    bbung_test_cards = make_test_cards(
        [3, 3, 5, 7, 9]
    )

    discarded_card = Card(
        month=3,
        copy_index=3,
    )

    matching_cards = get_bbung_cards(
        bbung_test_cards,
        discarded_card,
    )

    can_bbung = can_declare_bbung(
        bbung_test_cards,
        discarded_card,
    )

    bbung_test_months = [
        card.month
        for card in bbung_test_cards
    ]

    print(
        f"손패: "
        f"{bbung_test_months}"
    )

    print(
        f"상대 버림패: "
        f"{discarded_card.month}월"
    )

    print(
        f"같은 월 카드 수: "
        f"{len(matching_cards)}"
    )

    print(
        f"뻥 가능 여부: "
        f"{can_bbung}"
    )

    print()

    no_bbung_cards = make_test_cards(
        [3, 5, 7, 9, 11]
    )

    can_bbung = can_declare_bbung(
        no_bbung_cards,
        discarded_card,
    )

    no_bbung_months = [
        card.month
        for card in no_bbung_cards
    ]

    print(
        f"손패: "
        f"{no_bbung_months}"
    )

    print(
        f"상대 버림패: "
        f"{discarded_card.month}월"
    )

    print(
        f"뻥 가능 여부: "
        f"{can_bbung}"
    )

    # ============================================================
    # 11. GameEngine 뻥 후보 + 1초 반응창 테스트
    # ============================================================

    print()
    print("=== GameEngine 뻥 가능 여부 테스트 ===")

    bbung_game = create_test_game(
        game_id="TEST-BBUNG-ENGINE",
        owner_id="TEST-USER",
        human_nickname="뻥 테스트",
    )

    bbung_engine = GameEngine(
        bbung_game.state
    )

    dealer = (
        bbung_engine.get_current_player()
    )

    dealer.hand = make_test_cards(
        [3, 4, 5, 6, 7, 8]
    )

    bbung_game.state.players[1].hand = (
        make_test_cards(
            [3, 3, 5, 7, 9]
        )
    )

    bbung_game.state.players[2].hand = (
        make_test_cards(
            [3, 4, 6, 8, 10]
        )
    )

    dealer_three_card = next(
        card
        for card in dealer.hand
        if card.month == 3
    )

    bbung_engine.discard_card(
        dealer_three_card.card_id
    )

    ai1 = (
        bbung_game.state.players[1]
    )

    ai2 = (
        bbung_game.state.players[2]
    )

    ai1_can_bbung = (
        bbung_engine.can_player_declare_bbung(
            ai1.player_id
        )
    )

    ai2_can_bbung = (
        bbung_engine.can_player_declare_bbung(
            ai2.player_id
        )
    )

    dealer_can_bbung = (
        bbung_engine.can_player_declare_bbung(
            dealer.player_id
        )
    )

    print(
        f"마지막 버림패: "
        f"{bbung_game.state.last_discarded_card.month}월"
    )

    print(
        f"AI 1 뻥 가능: "
        f"{ai1_can_bbung}"
    )

    print(
        f"AI 2 뻥 가능: "
        f"{ai2_can_bbung}"
    )

    print(
        f"버린 본인 뻥 가능: "
        f"{dealer_can_bbung}"
    )

    print(
        f"뻥 후보 플레이어: "
        f"{bbung_game.state.bbung_candidate_player_ids}"
    )

    print(
        f"뻥 반응창 열림: "
        f"{bbung_game.state.bbung_reaction_open}"
    )

    print(
        f"실제 반응시간 활성: "
        f"{bbung_engine.is_bbung_reaction_active()}"
    )

    try:
        bbung_engine.advance_turn()
        print(
            "❌ 1초 이내 턴 이동 차단 실패"
        )
    except ValueError:
        print(
            "✅ 1초 이내 턴 이동 차단 성공"
        )

    time.sleep(1.1)

    print(
        f"1초 후 반응시간 활성: "
        f"{bbung_engine.is_bbung_reaction_active()}"
    )

    bbung_engine.advance_turn()

    next_player = (
        bbung_engine.get_current_player()
    )

    print(
        f"1초 후 다음 플레이어: "
        f"{next_player.player_id}"
    )

    print(
        f"다음 단계: "
        f"{bbung_game.state.turn_phase}"
    )

    # ============================================================
    # 12. 실제 뻥 선언 테스트
    # ============================================================

    print()
    print("=== GameEngine 실제 뻥 선언 테스트 ===")

    declare_bbung_game = create_test_game(
        game_id="TEST-DECLARE-BBUNG",
        owner_id="TEST-USER",
        human_nickname="뻥 선언 테스트",
    )

    declare_bbung_engine = GameEngine(
        declare_bbung_game.state
    )

    dealer = (
        declare_bbung_engine.get_current_player()
    )

    dealer.hand = make_test_cards(
        [3, 4, 5, 6, 7, 8]
    )

    bbung_player = (
        declare_bbung_game.state.players[1]
    )

    bbung_player.hand = make_test_cards(
        [3, 3, 5, 7, 9]
    )

    dealer_three_card = next(
        card
        for card in dealer.hand
        if card.month == 3
    )

    declare_bbung_engine.discard_card(
        dealer_three_card.card_id
    )

    matching_cards = [
        card
        for card in bbung_player.hand
        if card.month == 3
    ]

    extra_discard_card = next(
        card
        for card in bbung_player.hand
        if card.month == 9
    )

    hand_count_before = len(
        bbung_player.hand
    )

    discard_count_before = len(
        declare_bbung_game.state.discard_pile
    )

    discarded_cards = (
        declare_bbung_engine.declare_bbung(
            player_id=bbung_player.player_id,
            matching_card_ids=[
                card.card_id
                for card in matching_cards
            ],
            extra_discard_card_id=(
                extra_discard_card.card_id
            ),
        )
    )

    print(
        f"뻥 전 손패 수: "
        f"{hand_count_before}"
    )

    print(
        f"뻥 후 손패 수: "
        f"{len(bbung_player.hand)}"
    )

    discarded_months = [
        card.month
        for card in discarded_cards
    ]

    print(
        f"뻥으로 버린 카드: "
        f"{discarded_months}"
    )

    print(
        f"버림패 수: "
        f"{discard_count_before} -> "
        f"{len(declare_bbung_game.state.discard_pile)}"
    )

    print(
        f"뻥 이후 마지막 버림패: "
        f"{declare_bbung_game.state.last_discarded_card.month}월"
    )

    print(
        f"마지막 버린 플레이어: "
        f"{declare_bbung_game.state.last_discarded_by_player_id}"
    )

    print(
        f"현재 턴 기준 플레이어: "
        f"{declare_bbung_game.state.current_turn_player_id}"
    )

    print(
        f"현재 단계: "
        f"{declare_bbung_game.state.turn_phase}"
    )


    # 연속 뻥 체인 테스트
    print()
    print("=== 연속 뻥 체인 테스트 ===")

    chain_bbung_game = create_test_game(
        game_id="TEST-CHAIN-BBUNG",
        owner_id="TEST-USER",
        human_nickname="연속 뻥 테스트",
    )

    chain_bbung_engine = GameEngine(
        chain_bbung_game.state
    )

    p1 = chain_bbung_game.state.players[0]
    p2 = chain_bbung_game.state.players[1]
    p3 = chain_bbung_game.state.players[2]

    # P1은 3월 카드를 버린다.
    p1.hand = make_test_cards(
        [3, 4, 5, 6, 7, 8]
    )

    # P2는 3월 두 장으로 첫 번째 뻥 가능.
    # 추가 버림은 9월로 한다.
    p2.hand = make_test_cards(
        [3, 3, 5, 7, 9]
    )

    # P3은 9월 두 장을 가지고 있어서
    # P2의 추가 버림패 9월에 다시 뻥 가능.
    p3.hand = make_test_cards(
        [9, 9, 2, 4, 6]
    )

    p1_three_card = next(
        card
        for card in p1.hand
        if card.month == 3
    )

    chain_bbung_engine.discard_card(
        p1_three_card.card_id
    )

    print(
        f"P1 버림 후 뻥 후보: "
        f"{chain_bbung_game.state.bbung_candidate_player_ids}"
    )

    # P2 첫 번째 뻥
    p2_matching_cards = [
        card
        for card in p2.hand
        if card.month == 3
    ]

    p2_extra_card = next(
        card
        for card in p2.hand
        if card.month == 9
    )

    chain_bbung_engine.declare_bbung(
        player_id=p2.player_id,
        matching_card_ids=[
            card.card_id
            for card in p2_matching_cards
        ],
        extra_discard_card_id=(
            p2_extra_card.card_id
        ),
    )

    print(
        f"P2 뻥 후 마지막 버림패: "
        f"{chain_bbung_game.state.last_discarded_card.month}월"
    )

    print(
        f"P2 뻥 후 뻥 후보: "
        f"{chain_bbung_game.state.bbung_candidate_player_ids}"
    )

    print(
        f"P3 뻥 가능: "
        f"{chain_bbung_engine.can_player_declare_bbung(p3.player_id)}"
    )

    # P3 두 번째 뻥
    p3_matching_cards = [
        card
        for card in p3.hand
        if card.month == 9
    ]

    p3_extra_card = next(
        card
        for card in p3.hand
        if card.month == 6
    )

    chain_bbung_engine.declare_bbung(
        player_id=p3.player_id,
        matching_card_ids=[
            card.card_id
            for card in p3_matching_cards
        ],
        extra_discard_card_id=(
            p3_extra_card.card_id
        ),
    )

    print(
        f"P3 재뻥 후 마지막 버림패: "
        f"{chain_bbung_game.state.last_discarded_card.month}월"
    )

    print(
        f"P3 재뻥 후 현재 턴 기준: "
        f"{chain_bbung_game.state.current_turn_player_id}"
    )

    print(
        f"P3 재뻥 후 현재 단계: "
        f"{chain_bbung_game.state.turn_phase}"
    )

    print(
        f"P3 재뻥 후 뻥 후보: "
        f"{chain_bbung_game.state.bbung_candidate_player_ids}"
    )


    print(
        f"P2 뻥 횟수: "
        f"{p2.bbung_count}"
    )

    print(
        f"P2 뻥 월 기록: "
        f"{p2.bbung_months}"
    )

    print(
        f"P3 뻥 횟수: "
        f"{p3.bbung_count}"
    )

    print(
        f"P3 뻥 월 기록: "
        f"{p3.bbung_months}"
    )


    # ============================================================
    # 일반 바가지: 선언 / 철회 / 자동해제 / 재선언
    # ============================================================

    print()
    print("=== 일반 바가지 상태 관리 테스트 ===")

    bagaji_game = create_test_game(
        game_id="TEST-BAGAJI",
        owner_id="TEST-USER",
        human_nickname="바가지 테스트",
    )

    bagaji_engine = GameEngine(
        bagaji_game.state
    )

    p1 = bagaji_game.state.players[0]
    p2 = bagaji_game.state.players[1]
    p3 = bagaji_game.state.players[2]

    # 일반 바가지는 이번 라운드에
    # 최소 한 번 이상 뻥한 이력이 필요하다.
    p1.bbung_count = 1
    p2.bbung_count = 1
    p3.bbung_count = 1

    # 일반 바가지는 손패 전체가 정확히 2장이고
    # 그 2장이 같은 월이어야 한다.
    p1.hand = make_test_cards(
        [2, 2]
    )

    p2.hand = make_test_cards(
        [7, 7]
    )

    p3.hand = make_test_cards(
        [8, 8]
    )

    # 여러 플레이어는 각자 자기 바가지를
    # 하나씩 동시에 선언할 수 있다.
    bagaji_engine.declare_general_bagaji(
        player_id=p1.player_id,
        month=2,
    )

    bagaji_engine.declare_general_bagaji(
        player_id=p2.player_id,
        month=7,
    )

    bagaji_engine.declare_general_bagaji(
        player_id=p3.player_id,
        month=8,
    )

    declarations_after_first = [
        (
            declaration.player_id,
            declaration.month,
        )
        for declaration
        in bagaji_game.state.active_bagaji_declarations
    ]

    print(
        f"플레이어별 첫 선언 상태: "
        f"{declarations_after_first}"
    )

    print(
        f"활성 일반 바가지 수: "
        f"{len(declarations_after_first)}"
    )

    # P1이 직접 2월 바가지를 철회한다.
    cancelled = (
        bagaji_engine.cancel_general_bagaji(
            p1.player_id
        )
    )

    print(
        f"P1 직접 철회: "
        f"{cancelled.month}월"
    )

    # 손패는 여전히 [2, 2]이므로
    # 같은 2월 바가지를 다시 선언할 수 있다.
    redeclared = (
        bagaji_engine.declare_general_bagaji(
            player_id=p1.player_id,
            month=2,
        )
    )

    print(
        f"P1 같은 월 재선언: "
        f"{redeclared.month}월"
    )

    # 패가 한 장이라도 변하면 일반 바가지는 깨진다.
    # [2, 2] -> [2, 2, 1]
    temporary_card = Card(
        month=1,
        copy_index=1,
    )

    p1.hand.append(
        temporary_card
    )

    bagaji_engine.refresh_active_bagaji_declarations()

    p1_active_after_change = [
        declaration.month
        for declaration
        in bagaji_game.state.active_bagaji_declarations
        if declaration.player_id == p1.player_id
    ]

    print(
        f"P1 손패 [2,2,1] 후 활성 바가지: "
        f"{p1_active_after_change}"
    )

    # 다시 1월 카드를 버렸다고 가정해
    # 손패가 [2, 2]로 돌아오더라도
    # 자동 재선언되지는 않는다.
    p1.hand.remove(
        temporary_card
    )

    bagaji_engine.refresh_active_bagaji_declarations()

    p1_active_before_redeclare = [
        declaration.month
        for declaration
        in bagaji_game.state.active_bagaji_declarations
        if declaration.player_id == p1.player_id
    ]

    print(
        f"P1 다시 [2,2] 상태의 활성 바가지: "
        f"{p1_active_before_redeclare}"
    )

    # 조건이 다시 성립했으므로
    # 플레이어가 직접 다시 선언할 수 있다.
    bagaji_engine.declare_general_bagaji(
        player_id=p1.player_id,
        month=2,
    )

    final_general_declarations = [
        (
            declaration.player_id,
            declaration.month,
        )
        for declaration
        in bagaji_game.state.active_bagaji_declarations
    ]

    print(
        f"P1 재선언 후 최종 일반 바가지 상태: "
        f"{final_general_declarations}"
    )

    print()
    print("=== 게임 전체 카드 무결성 테스트 ===")

    integrity_game = create_test_game(
        game_id="TEST-INTEGRITY",
        owner_id="TEST-USER",
        human_nickname="무결성 테스트",
    )

    try:
        validate_game_card_integrity(
            integrity_game.state
        )

        print(
            "✅ 초기 분배 후 카드 무결성 정상"
        )

    except GameCardIntegrityError as error:
        print(
            f"❌ 카드 무결성 오류: "
            f"{error}"
        )


    integrity_engine = GameEngine(
        integrity_game.state
    )

    integrity_player = (
        integrity_engine.get_current_player()
    )

    discard_card_id = (
        integrity_player.hand[0].card_id
    )

    integrity_engine.discard_card(
        discard_card_id
    )

    try:
        validate_game_card_integrity(
            integrity_game.state
        )

        print(
            "✅ 카드 버리기 후 무결성 정상"
        )

    except GameCardIntegrityError as error:
        print(
            f"❌ 카드 버리기 후 무결성 오류: "
            f"{error}"
        )


    print()
    print("=== 일반 바가지 실제 발동 테스트 ===")

    trigger_bagaji_game = create_test_game(
        game_id="TEST-TRIGGER-BAGAJI",
        owner_id="TEST-USER",
        human_nickname="바가지 피해 테스트",
    )

    trigger_bagaji_engine = GameEngine(
        trigger_bagaji_game.state
    )

    victim = trigger_bagaji_game.state.players[0]
    bagaji_winner = (
        trigger_bagaji_game.state.players[1]
    )
    other_player = (
        trigger_bagaji_game.state.players[2]
    )

    # P1은 7월 카드를 버릴 예정.
    victim.hand = [
        Card(month=7, copy_index=3),
        Card(month=2, copy_index=1),
        Card(month=3, copy_index=1),
        Card(month=4, copy_index=1),
        Card(month=5, copy_index=1),
        Card(month=6, copy_index=1),
    ]

    # P2는 이미 뻥을 한 적이 있고,
    # 7월 두 장을 가지고 있어 7월 바가지 선언 가능.
    bagaji_winner.bbung_count = 1

    bagaji_winner.hand = [
        Card(month=7, copy_index=1),
        Card(month=7, copy_index=2),
    ]

    other_player.hand = [
        Card(month=1, copy_index=1),
        Card(month=10, copy_index=1),
        Card(month=11, copy_index=1),
        Card(month=12, copy_index=1),
    ]

    trigger_bagaji_engine.declare_general_bagaji(
        player_id=bagaji_winner.player_id,
        month=7,
    )

    victim_seven = next(
        card
        for card in victim.hand
        if card.month == 7
    )

    trigger_bagaji_engine.discard_card(
        victim_seven.card_id
    )

    print(
        f"게임 상태: "
        f"{trigger_bagaji_game.state.status}"
    )

    print(
        f"종료 이유: "
        f"{trigger_bagaji_game.state.round_end_reason}"
    )

    print(
        f"바가지 성공자: "
        f"{trigger_bagaji_game.state.round_winner_id}"
    )

    print(
        f"바가지 피해자: "
        f"{trigger_bagaji_game.state.bagaji_victim_id}"
    )

    print(
        f"발동 월: "
        f"{trigger_bagaji_game.state.triggered_bagaji_month}월"
    )

    print("플레이어별 점수:")

    for player in trigger_bagaji_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )


    print()
    print("=== 폭탄 바가지 선언 테스트 ===")

    bomb_bagaji_game = create_test_game(
        game_id="TEST-BOMB-BAGAJI",
        owner_id="TEST-USER",
        human_nickname="폭탄 바가지 테스트",
    )

    bomb_bagaji_engine = GameEngine(
        bomb_bagaji_game.state
    )

    bomb_bagaji_player = (
        bomb_bagaji_game.state.players[1]
    )

    # 3월 3장 = 폭탄
    # 7월 2장 = 바가지 대상
    bomb_bagaji_player.hand = [
        Card(month=3, copy_index=1),
        Card(month=3, copy_index=2),
        Card(month=3, copy_index=3),
        Card(month=7, copy_index=1),
        Card(month=7, copy_index=2),
    ]

    available_months = (
        get_bomb_bagaji_months(
            bomb_bagaji_player
        )
    )

    can_declare = (
        can_declare_bomb_bagaji(
            bomb_bagaji_player,
            7,
        )
    )

    declaration = (
        bomb_bagaji_engine.declare_bomb_bagaji(
            player_id=(
                bomb_bagaji_player.player_id
            ),
            month=7,
        )
    )

    print(
        f"폭탄 바가지 가능 월: "
        f"{available_months}"
    )

    print(
        f"7월 선언 가능: "
        f"{can_declare}"
    )

    print(
        f"선언 플레이어: "
        f"{declaration.player_id}"
    )

    print(
        f"폭탄 월: "
        f"{declaration.bomb_month}월"
    )

    print(
        f"바가지 대상 월: "
        f"{declaration.month}월"
    )

    # 폭탄 바가지도 선언 후 패 구성이 바뀌면
    # 즉시 자동 해제되어야 한다.
    temporary_bomb_card = Card(
        month=9,
        copy_index=1,
    )

    bomb_bagaji_player.hand.append(
        temporary_bomb_card
    )

    bomb_bagaji_engine.refresh_active_bagaji_declarations()

    bomb_active_after_change = [
        declaration.month
        for declaration
        in bomb_bagaji_game.state.active_bomb_bagaji_declarations
        if declaration.player_id
        == bomb_bagaji_player.player_id
    ]

    print(
        f"폭탄 바가지 손패 6장 변경 후 활성 상태: "
        f"{bomb_active_after_change}"
    )

    # 다시 원래 [3,3,3,7,7]로 돌아와도
    # 자동 재선언되지는 않는다.
    bomb_bagaji_player.hand.remove(
        temporary_bomb_card
    )

    bomb_bagaji_engine.refresh_active_bagaji_declarations()

    bomb_active_before_redeclare = [
        declaration.month
        for declaration
        in bomb_bagaji_game.state.active_bomb_bagaji_declarations
        if declaration.player_id
        == bomb_bagaji_player.player_id
    ]

    print(
        f"폭탄 바가지 원래 패 복구 후 활성 상태: "
        f"{bomb_active_before_redeclare}"
    )

    # 조건이 다시 성립했으므로 직접 재선언 가능.
    redeclared_bomb = (
        bomb_bagaji_engine.declare_bomb_bagaji(
            player_id=bomb_bagaji_player.player_id,
            month=7,
        )
    )

    print(
        f"폭탄 바가지 재선언 성공: "
        f"{redeclared_bomb.bomb_month}월 폭탄 + "
        f"{redeclared_bomb.month}월 바가지"
    )


    print()
    print("=== 폭탄 바가지 실제 발동 테스트 ===")

    trigger_bomb_bagaji_game = create_test_game(
        game_id="TEST-TRIGGER-BOMB-BAGAJI",
        owner_id="TEST-USER",
        human_nickname="폭탄 바가지 피해자",
    )

    trigger_bomb_bagaji_engine = GameEngine(
        trigger_bomb_bagaji_game.state
    )

    victim = (
        trigger_bomb_bagaji_game.state.players[0]
    )

    bomb_bagaji_winner = (
        trigger_bomb_bagaji_game.state.players[1]
    )

    other_player = (
        trigger_bomb_bagaji_game.state.players[2]
    )

    # P1은 7월을 버릴 예정.
    victim.hand = [
        Card(month=7, copy_index=3),
        Card(month=2, copy_index=1),
        Card(month=4, copy_index=1),
        Card(month=5, copy_index=1),
        Card(month=6, copy_index=1),
        Card(month=8, copy_index=1),
    ]

    # P2:
    # 3월 3장 = 폭탄
    # 7월 2장 = 폭탄 바가지 대상
    bomb_bagaji_winner.hand = [
        Card(month=3, copy_index=1),
        Card(month=3, copy_index=2),
        Card(month=3, copy_index=3),
        Card(month=7, copy_index=1),
        Card(month=7, copy_index=2),
    ]

    other_player.hand = [
        Card(month=1, copy_index=1),
        Card(month=9, copy_index=1),
        Card(month=10, copy_index=1),
        Card(month=11, copy_index=1),
        Card(month=12, copy_index=1),
    ]

    # 뻥 이력을 일부러 설정하지 않는다.
    # 폭탄 바가지는 뻥 이력이 없어도 선언 가능해야 한다.
    trigger_bomb_bagaji_engine.declare_bomb_bagaji(
        player_id=bomb_bagaji_winner.player_id,
        month=7,
    )

    victim_seven = next(
        card
        for card in victim.hand
        if card.month == 7
    )

    trigger_bomb_bagaji_engine.discard_card(
        victim_seven.card_id
    )

    print(
        f"게임 상태: "
        f"{trigger_bomb_bagaji_game.state.status}"
    )

    print(
        f"종료 이유: "
        f"{trigger_bomb_bagaji_game.state.round_end_reason}"
    )

    print(
        f"폭탄 바가지 성공자: "
        f"{trigger_bomb_bagaji_game.state.round_winner_id}"
    )

    print(
        f"피해자: "
        f"{trigger_bomb_bagaji_game.state.bagaji_victim_id}"
    )

    print(
        f"발동 월: "
        f"{trigger_bomb_bagaji_game.state.triggered_bagaji_month}월"
    )

    print("플레이어별 점수:")

    for player in (
        trigger_bomb_bagaji_game.state.players
    ):
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )


    print()
    print("=== 기습 STOP 조건 판정 테스트 ===")

    surprise_game = create_test_game(
        game_id="TEST-SURPRISE-STOP",
        owner_id="TEST-USER",
        human_nickname="기습 STOP 테스트",
    )

    p1 = surprise_game.state.players[0]
    p2 = surprise_game.state.players[1]
    p3 = surprise_game.state.players[2]

    # -----------------------------
    # 성공 케이스
    # 3인 게임:
    # 본인 포함 2명 이상 뻥 필요
    # -----------------------------

    p1.hand = make_test_cards(
        [2, 3]
    )

    p1.bbung_count = 1
    p2.bbung_count = 1
    p3.bbung_count = 0

    can_surprise = (
        can_declare_surprise_stop(
            p1,
            surprise_game.state.players,
        )
    )

    print(
        f"손패: "
        f"{[card.month for card in p1.hand]}"
    )

    print(
        f"두 장 합: "
        f"{calculate_two_card_sum(p1.hand)}"
    )

    print(
        f"뻥 플레이어 수: "
        f"{count_bbung_players(surprise_game.state.players)}"
    )

    print(
        f"기습 STOP 가능: "
        f"{can_surprise}"
    )

    # -----------------------------
    # 실패 케이스 1
    # 합계가 5 초과
    # -----------------------------

    p1.hand = make_test_cards(
        [3, 4]
    )

    can_surprise = (
        can_declare_surprise_stop(
            p1,
            surprise_game.state.players,
        )
    )

    print(
        f"합계 5 초과 시: "
        f"{can_surprise}"
    )

    # -----------------------------
    # 실패 케이스 2
    # 선언자 본인이 뻥하지 않음
    # -----------------------------

    p1.hand = make_test_cards(
        [2, 3]
    )

    p1.bbung_count = 0
    p2.bbung_count = 1
    p3.bbung_count = 1

    can_surprise = (
        can_declare_surprise_stop(
            p1,
            surprise_game.state.players,
        )
    )

    print(
        f"본인 뻥 없음: "
        f"{can_surprise}"
    )

    # -----------------------------
    # 실패 케이스 3
    # 뻥한 플레이어 수 부족
    # -----------------------------

    p1.bbung_count = 1
    p2.bbung_count = 0
    p3.bbung_count = 0

    can_surprise = (
        can_declare_surprise_stop(
            p1,
            surprise_game.state.players,
        )
    )

    print(
        f"뻥 인원 부족: "
        f"{can_surprise}"
    )


    print()
    print("=== GameEngine 기습 STOP 턴 검증 테스트 ===")

    surprise_engine_game = create_test_game(
        game_id="TEST-SURPRISE-ENGINE",
        owner_id="TEST-USER",
        human_nickname="기습 STOP 선언자",
    )

    surprise_engine = GameEngine(
        surprise_engine_game.state
    )

    p1 = surprise_engine_game.state.players[0]
    p2 = surprise_engine_game.state.players[1]
    p3 = surprise_engine_game.state.players[2]

    # P1이 기습 STOP 조건을 만족한다고 가정
    p1.hand = make_test_cards(
        [2, 3]
    )

    p1.bbung_count = 1
    p2.bbung_count = 1
    p3.bbung_count = 0

    # 테스트를 위해 P1의 차례 시작 상태로 설정
    surprise_engine_game.state.current_turn_player_id = (
        p1.player_id
    )

    surprise_engine_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    print(
        f"P1 본인 턴 기습 STOP 가능: "
        f"{surprise_engine.can_player_declare_surprise_stop(p1.player_id)}"
    )


    # 똑같은 조건이어도 P2 턴으로 바꾸면
    # P1은 선언할 수 없어야 한다.
    surprise_engine_game.state.current_turn_player_id = (
        p2.player_id
    )

    print(
        f"P1이 다른 사람 턴에 선언 가능: "
        f"{surprise_engine.can_player_declare_surprise_stop(p1.player_id)}"
    )


    print()
    print("=== 기습 STOP 실제 정산 테스트 ===")

    surprise_settle_game = create_test_game(
        game_id="TEST-SURPRISE-SETTLE",
        owner_id="TEST-USER",
        human_nickname="기습 STOP 정산",
    )

    surprise_settle_engine = GameEngine(
        surprise_settle_game.state
    )

    p1 = surprise_settle_game.state.players[0]
    p2 = surprise_settle_game.state.players[1]
    p3 = surprise_settle_game.state.players[2]

    # P1:
    # 기습 STOP 선언자
    # 2 + 3 = 5
    p1.hand = make_test_cards(
        [2, 3]
    )

    # P2:
    # 손패 점수 15
    p2.hand = make_test_cards(
        [1, 2, 3, 4, 5]
    )

    # P3:
    # 손패 점수 3
    # 선언자의 5점보다 낮으므로 독박 발생
    p3.hand = make_test_cards(
        [1, 2]
    )

    # 3인 게임이므로
    # 본인 포함 2명 이상 뻥
    p1.bbung_count = 1
    p2.bbung_count = 1
    p3.bbung_count = 0

    surprise_settle_game.state.current_turn_player_id = (
        p1.player_id
    )

    surprise_settle_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    final_score = (
        surprise_settle_engine.declare_surprise_stop(
            p1.player_id
        )
    )

    print(
        f"기습 STOP 기본 합: 5"
    )

    print(
        f"독박 여부: "
        f"{surprise_settle_game.state.surprise_stop_dokbak}"
    )

    print(
        f"선언자 최종 점수: "
        f"{final_score}"
    )

    print(
        f"게임 상태: "
        f"{surprise_settle_game.state.status}"
    )

    print(
        f"종료 이유: "
        f"{surprise_settle_game.state.round_end_reason}"
    )

    print("플레이어별 점수:")

    for player in surprise_settle_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )


    print()
    print("=== 기습 STOP 무독박 정산 테스트 ===")

    surprise_no_dokbak_game = create_test_game(
        game_id="TEST-SURPRISE-NO-DOKBAK",
        owner_id="TEST-USER",
        human_nickname="기습 STOP 무독박",
    )

    surprise_no_dokbak_engine = GameEngine(
        surprise_no_dokbak_game.state
    )

    p1 = surprise_no_dokbak_game.state.players[0]
    p2 = surprise_no_dokbak_game.state.players[1]
    p3 = surprise_no_dokbak_game.state.players[2]

    # P1:
    # 기습 STOP 선언자
    # 2 + 3 = 5
    p1.hand = make_test_cards(
        [2, 3]
    )

    # P2:
    # 손패 점수 15
    p2.hand = make_test_cards(
        [1, 2, 3, 4, 5]
    )

    # P3:
    # 손패 점수 11
    p3.hand = make_test_cards(
        [5, 6]
    )

    # 3인 게임:
    # 본인 포함 2명 이상 뻥 필요
    p1.bbung_count = 1
    p2.bbung_count = 1
    p3.bbung_count = 0

    surprise_no_dokbak_game.state.current_turn_player_id = (
        p1.player_id
    )

    surprise_no_dokbak_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    final_score = (
        surprise_no_dokbak_engine.declare_surprise_stop(
            p1.player_id
        )
    )

    print(
        f"기습 STOP 기본 합: 5"
    )

    print(
        f"독박 여부: "
        f"{surprise_no_dokbak_game.state.surprise_stop_dokbak}"
    )

    print(
        f"선언자 최종 점수: "
        f"{final_score}"
    )

    print(
        f"게임 상태: "
        f"{surprise_no_dokbak_game.state.status}"
    )

    print(
        f"종료 이유: "
        f"{surprise_no_dokbak_game.state.round_end_reason}"
    )

    print("플레이어별 점수:")

    for player in surprise_no_dokbak_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )


    print()
    print("=== 다음 라운드 시작 테스트 ===")

    next_round_game = create_test_game(
        game_id="TEST-NEXT-ROUND",
        owner_id="TEST-USER",
        human_nickname="다음 라운드 테스트",
    )

    next_round_engine = GameEngine(
        next_round_game.state
    )

    p1 = next_round_game.state.players[0]
    p2 = next_round_game.state.players[1]
    p3 = next_round_game.state.players[2]

    p1.hand = make_test_cards(
        [10, 10, 11, 11, 12, 12]
    )

    p2.hand = make_test_cards(
        [1, 2, 3, 4, 5]
    )

    p3.hand = make_test_cards(
        [6, 7, 8, 9, 10]
    )

    next_round_engine.declare_stop(
        StopType.HIGH_SUM
    )

    print(
        f"1라운드 종료 상태: "
        f"{next_round_game.state.status}"
    )

    print(
        f"1라운드 번호: "
        f"{next_round_game.state.round_number}"
    )

    print("1라운드 누적 점수:")

    for player in next_round_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.total_score}점"
        )

    totals_before_next_round = {
        player.player_id: player.total_score
        for player in next_round_game.state.players
    }

    next_round_engine.start_next_round(
        next_dealer_id=p2.player_id
    )

    print(
        "덱 재셔플 사용 기록 초기화:",
        next_round_game.state.deck_reshuffle_used
        is False,
    )

    print()
    print(
        f"2라운드 번호: "
        f"{next_round_game.state.round_number}"
    )

    print(
        f"2라운드 상태: "
        f"{next_round_game.state.status}"
    )

    print(
        f"2라운드 선: "
        f"{next_round_game.state.dealer_id}"
    )

    print(
        f"현재 턴 플레이어: "
        f"{next_round_game.state.current_turn_player_id}"
    )

    print(
        f"현재 단계: "
        f"{next_round_game.state.turn_phase}"
    )

    print("새 라운드 카드 수:")

    for player in next_round_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{len(player.hand)}장"
        )

    print(
        f"남은 덱: "
        f"{len(next_round_game.state.deck.cards)}장"
    )

    print("2라운드 round_score:")

    for player in next_round_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )

    print("누적 점수 유지 검사:")

    for player in next_round_game.state.players:
        before_score = totals_before_next_round[
            player.player_id
        ]

        passed = (
            player.total_score
            == before_score
        )

        print(
            f"  {player.nickname}: "
            f"{player.total_score}점 / "
            f"{'✅ 유지' if passed else '❌ 변경됨'}"
        )

    print(
        f"뻥 선언 기록 초기화: "
        f"{all(player.bbung_count == 0 for player in next_round_game.state.players)}"
    )

    print(
        f"일반 바가지 선언 초기화: "
        f"{len(next_round_game.state.active_bagaji_declarations) == 0}"
    )

    print(
        f"폭탄 바가지 선언 초기화: "
        f"{len(next_round_game.state.active_bomb_bagaji_declarations) == 0}"
    )

    print(
        f"이전 라운드 종료 이유 초기화: "
        f"{next_round_game.state.round_end_reason is None}"
    )

    print(
        f"라운드 정산 플래그 초기화: "
        f"{next_round_game.state.round_finalized is False}"
    )


    print()
    print("=== 20라운드 단독 우승 테스트 ===")

    solo_winner_game = create_test_game(
        game_id="TEST-SOLO-WINNER",
        owner_id="TEST-USER",
        human_nickname="단독 우승 테스트",
    )

    solo_winner_engine = GameEngine(
        solo_winner_game.state
    )

    p1 = solo_winner_game.state.players[0]
    p2 = solo_winner_game.state.players[1]
    p3 = solo_winner_game.state.players[2]

    solo_winner_game.state.round_number = 20
    solo_winner_game.state.status = (
        GameStatus.ROUND_END
    )
    solo_winner_game.state.round_finalized = True

    p1.total_score = -120
    p2.total_score = -80
    p3.total_score = 10

    solo_winner_engine.start_game_end_sequence()

    print(
        f"게임 상태: "
        f"{solo_winner_game.state.status}"
    )

    print(
        f"최종 우승자: "
        f"{solo_winner_game.state.game_winner_id}"
    )


    print()
    print("=== 20라운드 동점 → 타이브레이커 테스트 ===")

    tie_break_game = create_test_game(
        game_id="TEST-TIE-BREAK",
        owner_id="TEST-USER",
        human_nickname="타이브레이커 테스트",
    )

    tie_break_engine = GameEngine(
        tie_break_game.state
    )

    p1 = tie_break_game.state.players[0]
    p2 = tie_break_game.state.players[1]
    p3 = tie_break_game.state.players[2]

    tie_break_game.state.round_number = 20
    tie_break_game.state.status = (
        GameStatus.ROUND_END
    )
    tie_break_game.state.round_finalized = True

    p1.total_score = -150
    p2.total_score = -150
    p3.total_score = -30

    tie_break_engine.start_game_end_sequence()

    print(
        f"게임 상태: "
        f"{tie_break_game.state.status}"
    )

    print(
        f"타이브레이커 참가자: "
        f"{tie_break_game.state.tie_break_player_ids}"
    )

    print(
        f"타이브레이커 라운드: "
        f"{tie_break_game.state.tie_break_round_number}"
    )

    print(
        f"현재 인덱스: "
        f"{tie_break_game.state.tie_break_current_player_index}"
    )

    print(
        f"뽑은 카드 상태: "
        f"{tie_break_game.state.tie_break_drawn_cards}"
    )

    print()
    print("=== 타이브레이커 공개 드로우 테스트 ===")

    draw_game = create_test_game(
        game_id="TEST-TIE-BREAK-DRAW",
        owner_id="TEST-USER",
        human_nickname="미니게임 P1",
    )

    draw_engine = GameEngine(
        draw_game.state
    )

    p1 = draw_game.state.players[0]
    p2 = draw_game.state.players[1]
    p3 = draw_game.state.players[2]

    # 20라운드 종료 후
    # P1 / P2가 공동 최저점이라고 가정
    draw_game.state.round_number = 20
    draw_game.state.status = (
        GameStatus.ROUND_END
    )
    draw_game.state.round_finalized = True

    p1.total_score = -100
    p2.total_score = -100
    p3.total_score = 20

    draw_engine.start_game_end_sequence()

    print(
        f"미니게임 시작 상태: "
        f"{draw_game.state.status}"
    )

    print(
        f"참가자: "
        f"{draw_game.state.tie_break_player_ids}"
    )

    # P1 → P2 → P1 → P2 → P1 → P2
    # 순서대로 총 6번 뽑는다.
    while draw_game.state.status == GameStatus.TIE_BREAK:
        current_player_id = (
            draw_engine
            .get_current_tie_break_player_id()
        )

        # 드로우하기 전 상태를 복사해 둔다.
        # 세 번째 카드가 동점으로 끝나면 엔진이 즉시
        # 다음 타이브레이커 라운드로 초기화하기 때문이다.
        before_cards = list(
            draw_game.state
            .tie_break_drawn_cards[
                current_player_id
            ]
        )

        before_round_number = (
            draw_game.state.tie_break_round_number
        )

        card = draw_engine.draw_tie_break_card(
            current_player_id
        )

        displayed_months = [
            target.month
            for target in before_cards
        ]

        displayed_months.append(
            card.month
        )

        displayed_score = sum(
            displayed_months
        )

        print(
            f"{current_player_id} "
            f"→ {card.month}월 공개"
        )

        print(
            f"  현재 카드: "
            f"{displayed_months}"
        )

        print(
            f"  현재 합계: "
            f"{displayed_score}"
        )

        # 세 번째 카드까지 뽑은 뒤에도
        # 게임이 TIE_BREAK 상태라면 재동점이 발생한 것.
        if (
            len(displayed_months) == 3
            and draw_game.state.status
            == GameStatus.TIE_BREAK
            and draw_game.state.tie_break_round_number
            > before_round_number
        ):
            print()
            print(
                "🔁 최고 합계 동점 발생"
            )

            print(
                f"→ 타이브레이커 "
                f"{draw_game.state.tie_break_round_number}"
                f"라운드 시작"
            )

            print(
                f"재대결 참가자: "
                f"{draw_game.state.tie_break_player_ids}"
            )

            print()

    print()
    print(
        f"최종 게임 상태: "
        f"{draw_game.state.status}"
    )

    print(
        f"최종 우승자: "
        f"{draw_game.state.game_winner_id}"
    )



    print()
    print("=== 3인 첫 덱 소진 재셔플 테스트 ===")

    reshuffle_game = create_test_game(
        game_id="TEST-DECK-RESHUFFLE",
        owner_id="TEST-USER",
        human_nickname="재셔플 테스트",
    )

    reshuffle_engine = GameEngine(
        reshuffle_game.state
    )

    p1 = reshuffle_game.state.players[0]
    p2 = reshuffle_game.state.players[1]

    # P2의 드로우 차례라고 가정
    reshuffle_game.state.current_turn_player_id = (
        p2.player_id
    )

    reshuffle_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    # 기존 덱은 완전히 소진된 상태
    reshuffle_game.state.deck.cards.clear()

    # 테스트용 버림패 3장
    reshuffle_game.state.discard_pile = [
        Card(month=2, copy_index=1),
        Card(month=7, copy_index=1),
        Card(month=11, copy_index=1),
    ]

    reshuffle_game.state.deck_reshuffle_used = False

    print(
        f"재셔플 전 덱: "
        f"{len(reshuffle_game.state.deck.cards)}장"
    )

    print(
        f"재셔플 전 버림패: "
        f"{len(reshuffle_game.state.discard_pile)}장"
    )

    drawn_card = (
        reshuffle_engine.draw_card()
    )

    print(
        f"드로우 카드: "
        f"{drawn_card.month}월"
    )

    print(
        f"재셔플 사용 여부: "
        f"{reshuffle_game.state.deck_reshuffle_used}"
    )

    print(
        f"드로우 후 덱: "
        f"{len(reshuffle_game.state.deck.cards)}장"
    )

    print(
        f"드로우 후 버림패: "
        f"{len(reshuffle_game.state.discard_pile)}장"
    )

    print(
        f"게임 상태: "
        f"{reshuffle_game.state.status}"
    )

    print(
        f"현재 단계: "
        f"{reshuffle_game.state.turn_phase}"
    )



    print()
    print("=== 3인 두 번째 덱 소진 종료 테스트 ===")

    exhausted_game = create_test_game(
        game_id="TEST-DECK-EXHAUSTED",
        owner_id="TEST-USER",
        human_nickname="덱 소진 테스트",
    )

    exhausted_engine = GameEngine(
        exhausted_game.state
    )

    p1 = exhausted_game.state.players[0]
    p2 = exhausted_game.state.players[1]
    p3 = exhausted_game.state.players[2]

    p1.hand = make_test_cards(
        [1, 2, 3]
    )

    p2.hand = make_test_cards(
        [4, 5]
    )

    p3.hand = make_test_cards(
        [6, 7]
    )

    exhausted_game.state.current_turn_player_id = (
        p1.player_id
    )

    exhausted_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    exhausted_game.state.deck.cards.clear()

    exhausted_game.state.deck_reshuffle_used = True

    result = exhausted_engine.draw_card()

    print(
        f"드로우 결과: "
        f"{result}"
    )

    print(
        f"게임 상태: "
        f"{exhausted_game.state.status}"
    )

    print(
        f"종료 이유: "
        f"{exhausted_game.state.round_end_reason}"
    )

    print(
        f"라운드 승자: "
        f"{exhausted_game.state.round_winner_id}"
    )

    print("플레이어별 점수:")

    for player in exhausted_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )

    print()
    print("=== 4인 덱 소진 즉시 종료 테스트 ===")

    four_player_game = create_test_game(
        game_id="TEST-4P-DECK-EXHAUSTED",
        owner_id="TEST-USER",
        human_nickname="4인 덱 소진 테스트",
    )

    # 기존 3인 테스트 게임에 플레이어 1명 추가
    four_player_game.state.players.append(
        Player(
            player_id="TEST-4P-DECK-EXHAUSTED-P4",
            nickname="AI 3",
            player_type=PlayerType.BOT,
        )
    )

    four_player_engine = GameEngine(
        four_player_game.state
    )

    p1 = four_player_game.state.players[0]
    p2 = four_player_game.state.players[1]
    p3 = four_player_game.state.players[2]
    p4 = four_player_game.state.players[3]

    # 덱 소진 시 계산할 손패를 테스트용으로 지정
    p1.hand = make_test_cards(
        [1, 2, 3]
    )

    p2.hand = make_test_cards(
        [4, 5]
    )

    p3.hand = make_test_cards(
        [6, 7]
    )

    p4.hand = make_test_cards(
        [8, 9]
    )

    four_player_game.state.current_turn_player_id = (
        p1.player_id
    )

    four_player_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    # 첫 번째 덱이 이미 소진된 상태
    four_player_game.state.deck.cards.clear()

    # 4인 게임에서는 이 값과 관계없이
    # 재셔플 없이 즉시 종료되어야 한다.
    four_player_game.state.deck_reshuffle_used = False

    result = four_player_engine.draw_card()

    print(
        f"드로우 결과: "
        f"{result}"
    )

    print(
        f"게임 상태: "
        f"{four_player_game.state.status}"
    )

    print(
        f"종료 이유: "
        f"{four_player_game.state.round_end_reason}"
    )

    print(
        f"라운드 승자: "
        f"{four_player_game.state.round_winner_id}"
    )

    print(
        f"재셔플 사용 여부: "
        f"{four_player_game.state.deck_reshuffle_used}"
    )

    print("플레이어별 점수:")

    for player in four_player_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )


    print()
    print("=== 라운드 자동 진행 테스트 ===")

    continue_game = create_test_game(
        game_id="TEST-CONTINUE-ROUND",
        owner_id="TEST-USER",
        human_nickname="자동 진행 테스트",
    )

    continue_engine = GameEngine(
        continue_game.state
    )

    p1 = continue_game.state.players[0]
    p2 = continue_game.state.players[1]
    p3 = continue_game.state.players[2]

    continue_game.state.round_number = 19

    continue_game.state.status = (
        GameStatus.ROUND_END
    )

    continue_game.state.round_finalized = True

    p1.total_score = -50
    p2.total_score = -20
    p3.total_score = 10

    continue_engine.continue_after_round(
        next_dealer_id=p2.player_id
    )

    print(
        f"라운드 번호: "
        f"{continue_game.state.round_number}"
    )

    print(
        f"게임 상태: "
        f"{continue_game.state.status}"
    )

    print(
        f"20라운드 선: "
        f"{continue_game.state.dealer_id}"
    )

    print(
        f"현재 턴: "
        f"{continue_game.state.current_turn_player_id}"
    )



    print()
    print("=== 20라운드 종료 자동 최종 판정 테스트 ===")

    final_continue_game = create_test_game(
        game_id="TEST-FINAL-CONTINUE",
        owner_id="TEST-USER",
        human_nickname="최종 자동 진행 테스트",
    )

    final_continue_engine = GameEngine(
        final_continue_game.state
    )

    p1 = final_continue_game.state.players[0]
    p2 = final_continue_game.state.players[1]
    p3 = final_continue_game.state.players[2]

    final_continue_game.state.round_number = 20

    final_continue_game.state.status = (
        GameStatus.ROUND_END
    )

    final_continue_game.state.round_finalized = True

    p1.total_score = -120
    p2.total_score = -80
    p3.total_score = 20

    final_continue_engine.continue_after_round()

    print(
        f"게임 상태: "
        f"{final_continue_game.state.status}"
    )

    print(
        f"최종 우승자: "
        f"{final_continue_game.state.game_winner_id}"
    )


    print()
    print("=== 다음 선 미확정 규칙 차단 테스트 ===")

    dealer_rule_game = create_test_game(
        game_id="TEST-DEALER-RULE",
        owner_id="TEST-USER",
        human_nickname="다음 선 테스트",
    )

    dealer_rule_engine = GameEngine(
        dealer_rule_game.state
    )

    p1 = dealer_rule_game.state.players[0]

    dealer_rule_game.state.status = (
        GameStatus.ROUND_END
    )

    dealer_rule_game.state.round_finalized = True

    dealer_rule_game.state.round_winner_id = (
        p1.player_id
    )

    dealer_rule_game.state.round_end_reason = (
        RoundEndReason.NORMAL_STOP
    )

    try:
        dealer_rule_engine.determine_next_dealer_id()

        print(
            "❌ 미확정 선 규칙 차단 실패"
        )

    except ValueError as error:
        print(
            "✅ 미확정 선 규칙 차단 성공"
        )

        print(
            f"  사유: {error}"
        )


    print()
    print("=== AI 난이도 상태 테스트 ===")

    ai_state_game = create_test_game(
        game_id="TEST-AI-STATE",
        owner_id="TEST-USER",
        human_nickname="AI 상태 테스트",
    )

    human = ai_state_game.state.players[0]
    ai1 = ai_state_game.state.players[1]
    ai2 = ai_state_game.state.players[2]

    print(
        f"사람 플레이어 AI 난이도: "
        f"{human.ai_difficulty}"
    )

    print(
        f"AI 1 난이도: "
        f"{ai1.ai_difficulty.display_name}"
    )

    print(
        f"AI 2 난이도: "
        f"{ai2.ai_difficulty.display_name}"
    )

    print()
    print("=== 초보 AI 버림패 선택 테스트 ===")

    beginner_ai_game = create_test_game(
        game_id="TEST-BEGINNER-AI",
        owner_id="TEST-USER",
        human_nickname="AI 테스트",
    )

    beginner_ai = (
        beginner_ai_game.state.players[1]
    )

    beginner_ai.hand = make_test_cards(
        [2, 5, 11, 7, 3, 9]
    )

    selected_card = choose_beginner_discard(
        beginner_ai
    )

    hand_months = [
        card.month
        for card in beginner_ai.hand
    ]

    print(
        f"AI 손패: "
        f"{hand_months}"
    )

    print(
        f"AI 선택 카드: "
        f"{selected_card.month}월"
    )

    print(
        f"선택 카드 ID: "
        f"{selected_card.card_id}"
    )

    print(
        f"선택 후 손패 수: "
        f"{len(beginner_ai.hand)}장"
    )

    print()
    print("=== 초보 AI 실제 버리기 테스트 ===")

    ai_discard_game = create_test_game(
        game_id="TEST-AI-DISCARD",
        owner_id="TEST-USER",
        human_nickname="AI 버리기 테스트",
    )

    ai_discard_engine = GameEngine(
        ai_discard_game.state
    )

    ai_player = (
        ai_discard_game.state.players[1]
    )

    ai_player.hand = make_test_cards(
        [2, 5, 11, 7, 3, 9]
    )

    ai_discard_game.state.current_turn_player_id = (
        ai_player.player_id
    )

    ai_discard_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    print(
        f"버리기 전 손패 수: "
        f"{len(ai_player.hand)}장"
    )

    selected_card = (
        ai_discard_engine
        .play_beginner_ai_discard(
            ai_player.player_id
        )
    )

    remaining_months = [
        card.month
        for card in ai_player.hand
    ]

    print(
        f"AI가 실제로 버린 카드: "
        f"{selected_card.month}월"
    )

    print(
        f"버리기 후 손패: "
        f"{remaining_months}"
    )

    print(
        f"버리기 후 손패 수: "
        f"{len(ai_player.hand)}장"
    )

    print(
        f"마지막 버림패: "
        f"{ai_discard_game.state.last_discarded_card.month}월"
    )

    print(
        f"현재 단계: "
        f"{ai_discard_game.state.turn_phase}"
    )


    print()
    print("=== 초보 AI 전체 턴 테스트 ===")

    ai_turn_game = create_test_game(
        game_id="TEST-AI-TURN",
        owner_id="TEST-USER",
        human_nickname="AI 턴 테스트",
    )

    ai_turn_engine = GameEngine(
        ai_turn_game.state
    )

    ai_player = (
        ai_turn_game.state.players[1]
    )

    ai_player.hand = make_test_cards(
        [2, 5, 7, 3, 9]
    )

    ai_turn_game.state.current_turn_player_id = (
        ai_player.player_id
    )

    ai_turn_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    print(
        f"턴 시작 손패 수: "
        f"{len(ai_player.hand)}장"
    )

    print(
        f"턴 시작 단계: "
        f"{ai_turn_game.state.turn_phase}"
    )

    discarded_card = (
        ai_turn_engine.play_beginner_ai_turn(
            ai_player.player_id
        )
    )

    remaining_months = [
        card.month
        for card in ai_player.hand
    ]

    print(
        f"AI가 버린 카드: "
        f"{discarded_card.month}월"
    )

    print(
        f"턴 종료 손패: "
        f"{remaining_months}"
    )

    print(
        f"턴 종료 손패 수: "
        f"{len(ai_player.hand)}장"
    )

    print(
        f"마지막 버림패: "
        f"{ai_turn_game.state.last_discarded_card.month}월"
    )

    print(
        f"턴 종료 단계: "
        f"{ai_turn_game.state.turn_phase}"
    )

    print()
    print("=== 초보 AI STOP 자동 선언 테스트 ===")

    ai_stop_game = create_test_game(
        game_id="TEST-AI-STOP",
        owner_id="TEST-USER",
        human_nickname="AI STOP 테스트",
    )

    ai_stop_engine = GameEngine(
        ai_stop_game.state
    )

    ai_player = (
        ai_stop_game.state.players[1]
    )

    # STOP 가능한 6장
    ai_player.hand = make_test_cards(
        [10, 10, 11, 11, 12, 12]
    )

    ai_stop_game.state.current_turn_player_id = (
        ai_player.player_id
    )

    ai_stop_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    ai_stop_months = [
        card.month
        for card in ai_player.hand
    ]

    print(
        f"AI 손패: "
        f"{ai_stop_months}"
    )


    result = (
        ai_stop_engine.play_beginner_ai_turn(
            ai_player.player_id
        )
    )

    print(
        f"AI 턴 반환값: "
        f"{result}"
    )

    print(
        f"게임 상태: "
        f"{ai_stop_game.state.status}"
    )

    print(
        f"선언된 STOP: "
        f"{ai_stop_game.state.declared_stop_type}"
    )

    print(
        f"라운드 승자: "
        f"{ai_stop_game.state.round_winner_id}"
    )

    print(
        f"AI 라운드 점수: "
        f"{ai_player.round_score}"
    )


    print()
    print("=== 초보 AI 자동 뻥 테스트 ===")

    ai_bbung_game = create_test_game(
        game_id="TEST-AI-BBUNG",
        owner_id="TEST-USER",
        human_nickname="AI 뻥 테스트",
    )

    ai_bbung_engine = GameEngine(
        ai_bbung_game.state
    )

    human = ai_bbung_game.state.players[0]
    ai_player = ai_bbung_game.state.players[1]
    other_ai = ai_bbung_game.state.players[2]

    human.hand = make_test_cards(
        [3, 4, 5, 6, 7, 8]
    )

    ai_player.hand = make_test_cards(
        [3, 3, 5, 7, 9]
    )

    other_ai.hand = make_test_cards(
        [1, 2, 4, 6, 8]
    )

    ai_bbung_game.state.current_turn_player_id = (
        human.player_id
    )

    ai_bbung_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    human_three = next(
        card
        for card in human.hand
        if card.month == 3
    )

    ai_bbung_engine.discard_card(
        human_three.card_id
    )

    print(
        f"AI 뻥 가능: "
        f"{ai_bbung_engine.can_player_declare_bbung(ai_player.player_id)}"
    )

    print(
        f"뻥 전 AI 손패 수: "
        f"{len(ai_player.hand)}장"
    )

    bbung_result = (
        ai_bbung_engine.try_beginner_ai_bbung(
            ai_player.player_id
        )
    )

    remaining_months = [
        card.month
        for card in ai_player.hand
    ]

    print(
        f"AI 뻥 실행: "
        f"{bbung_result}"
    )

    print(
        f"뻥 후 AI 손패: "
        f"{remaining_months}"
    )

    print(
        f"뻥 후 AI 손패 수: "
        f"{len(ai_player.hand)}장"
    )

    print(
        f"AI 뻥 횟수: "
        f"{ai_player.bbung_count}"
    )

    print(
        f"AI 뻥 월 기록: "
        f"{ai_player.bbung_months}"
    )

    print(
        f"새 마지막 버림패: "
        f"{ai_bbung_game.state.last_discarded_card.month}월"
    )

    print(
        f"현재 단계: "
        f"{ai_bbung_game.state.turn_phase}"
    )


    print()
    print("=== 초보 AI 자동 뻥 반응 연결 테스트 ===")

    auto_bbung_game = create_test_game(
        game_id="TEST-AUTO-AI-BBUNG",
        owner_id="TEST-USER",
        human_nickname="자동 뻥 테스트",
    )

    auto_bbung_engine = GameEngine(
        auto_bbung_game.state
    )

    human = auto_bbung_game.state.players[0]
    ai_player = auto_bbung_game.state.players[1]
    other_ai = auto_bbung_game.state.players[2]

    human.hand = make_test_cards(
        [3, 4, 5, 6, 7, 8]
    )

    # AI 1만 3월 두 장을 가지고 있어서
    # 뻥 후보가 된다.
    ai_player.hand = make_test_cards(
        [3, 3, 5, 7, 9]
    )

    # AI 2는 3월 두 장이 없으므로
    # 뻥 후보가 아니다.
    other_ai.hand = make_test_cards(
        [1, 2, 4, 6, 8]
    )

    auto_bbung_game.state.current_turn_player_id = (
        human.player_id
    )

    auto_bbung_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    human_three = next(
        card
        for card in human.hand
        if card.month == 3
    )

    auto_bbung_engine.discard_card(
        human_three.card_id
    )

    candidates_before = list(
        auto_bbung_game.state
        .bbung_candidate_player_ids
    )

    print(
        f"자동 처리 전 뻥 후보: "
        f"{candidates_before}"
    )

    auto_result = (
        auto_bbung_engine
        .process_beginner_ai_bbung_reaction()
    )

    remaining_months = [
        card.month
        for card in ai_player.hand
    ]

    print(
        f"AI 자동 뻥 실행: "
        f"{auto_result}"
    )

    print(
        f"AI 남은 손패: "
        f"{remaining_months}"
    )

    print(
        f"AI 뻥 횟수: "
        f"{ai_player.bbung_count}"
    )

    print(
        f"새 마지막 버림패: "
        f"{auto_bbung_game.state.last_discarded_card.month}월"
    )

    print(
        f"현재 턴 기준 플레이어: "
        f"{auto_bbung_game.state.current_turn_player_id}"
    )

    print(
        f"현재 단계: "
        f"{auto_bbung_game.state.turn_phase}"
    )


    print()
    print("=== 초보 AI 연속 자동 뻥 테스트 ===")

    chain_ai_game = create_test_game(
        game_id="TEST-AI-BBUNG-CHAIN",
        owner_id="TEST-USER",
        human_nickname="연속 자동 뻥 테스트",
    )

    chain_ai_engine = GameEngine(
        chain_ai_game.state
    )

    p1 = chain_ai_game.state.players[0]
    p2 = chain_ai_game.state.players[1]
    p3 = chain_ai_game.state.players[2]

    # P1이 3월을 버린다.
    p1.hand = make_test_cards(
        [3, 4, 5, 6, 7, 8]
    )

    # P2:
    # 3월 두 장으로 첫 번째 뻥
    # 남은 카드 중 가장 큰 9월을 추가 버림
    p2.hand = make_test_cards(
        [3, 3, 5, 7, 9]
    )

    # P3:
    # P2가 버린 9월에 다시 뻥
    # 남은 카드 중 가장 큰 6월을 추가 버림
    p3.hand = make_test_cards(
        [9, 9, 2, 4, 6]
    )

    chain_ai_game.state.current_turn_player_id = (
        p1.player_id
    )

    chain_ai_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    p1_three = next(
        card
        for card in p1.hand
        if card.month == 3
    )

    chain_ai_engine.discard_card(
        p1_three.card_id
    )

    print(
        f"첫 번째 버림패: "
        f"{chain_ai_game.state.last_discarded_card.month}월"
    )

    auto_bbung_count = (
        chain_ai_engine
        .process_all_beginner_ai_bbung_reactions()
    )

    p2_months = [
        card.month
        for card in p2.hand
    ]

    p3_months = [
        card.month
        for card in p3.hand
    ]

    print(
        f"자동 뻥 횟수: "
        f"{auto_bbung_count}"
    )

    print(
        f"P2 남은 손패: "
        f"{p2_months}"
    )

    print(
        f"P2 뻥 횟수: "
        f"{p2.bbung_count}"
    )

    print(
        f"P3 남은 손패: "
        f"{p3_months}"
    )

    print(
        f"P3 뻥 횟수: "
        f"{p3.bbung_count}"
    )

    print(
        f"최종 마지막 버림패: "
        f"{chain_ai_game.state.last_discarded_card.month}월"
    )

    print(
        f"최종 턴 기준 플레이어: "
        f"{chain_ai_game.state.current_turn_player_id}"
    )

    print(
        f"최종 단계: "
        f"{chain_ai_game.state.turn_phase}"
    )


    print()
    print("=== 초보 AI 뻥 후 다음 턴 자동 진행 테스트 ===")

    flow_game = create_test_game(
        game_id="TEST-AI-REACTION-FLOW",
        owner_id="TEST-USER",
        human_nickname="반응 흐름 테스트",
    )

    flow_engine = GameEngine(
        flow_game.state
    )

    p1 = flow_game.state.players[0]
    p2 = flow_game.state.players[1]
    p3 = flow_game.state.players[2]

    # P1이 3월을 버린다.
    p1.hand = make_test_cards(
        [3, 4, 5, 6, 7, 8]
    )

    # P2는 3월 두 장으로 뻥.
    # 초보 AI이므로 남은 카드 중
    # 가장 큰 9월을 추가로 버린다.
    p2.hand = make_test_cards(
        [3, 3, 5, 7, 9]
    )

    # P3은 9월 뻥이 불가능하다.
    p3.hand = make_test_cards(
        [1, 2, 4, 6, 8]
    )

    flow_game.state.current_turn_player_id = (
        p1.player_id
    )

    flow_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    p1_three = next(
        card
        for card in p1.hand
        if card.month == 3
    )

    flow_engine.discard_card(
        p1_three.card_id
    )

    print(
        f"P1 버림 후 단계: "
        f"{flow_game.state.turn_phase}"
    )

    print(
        f"P1 버림 후 후보: "
        f"{flow_game.state.bbung_candidate_player_ids}"
    )

    bbung_count = (
        flow_engine.resolve_beginner_ai_reaction_flow()
    )

    p2_months = [
        card.month
        for card in p2.hand
    ]

    print(
        f"자동 뻥 횟수: "
        f"{bbung_count}"
    )

    print(
        f"P2 남은 손패: "
        f"{p2_months}"
    )

    print(
        f"최종 마지막 버림패: "
        f"{flow_game.state.last_discarded_card.month}월"
    )

    print(
        f"현재 플레이어: "
        f"{flow_game.state.current_turn_player_id}"
    )

    print(
        f"현재 단계: "
        f"{flow_game.state.turn_phase}"
    )


    print()
    print("=== 초보 AI 연속 턴 자동 진행 테스트 ===")

    auto_turn_game = create_test_game(
        game_id="TEST-AI-AUTO-TURNS",
        owner_id="TEST-USER",
        human_nickname="사람 플레이어",
    )

    auto_turn_engine = GameEngine(
        auto_turn_game.state
    )

    p1 = auto_turn_game.state.players[0]
    p2 = auto_turn_game.state.players[1]
    p3 = auto_turn_game.state.players[2]

    # 테스트를 위해 P2 차례부터 시작
    auto_turn_game.state.current_turn_player_id = (
        p2.player_id
    )

    auto_turn_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    print(
        f"자동 진행 시작 플레이어: "
        f"{auto_turn_game.state.current_turn_player_id}"
    )

    print(
        f"자동 진행 시작 단계: "
        f"{auto_turn_game.state.turn_phase}"
    )

    ai_turn_count = (
        auto_turn_engine
        .run_beginner_ai_until_human_turn()
    )

    print(
        f"자동 처리된 AI 턴 수: "
        f"{ai_turn_count}"
    )

    print(
        f"자동 진행 후 플레이어: "
        f"{auto_turn_game.state.current_turn_player_id}"
    )

    print(
        f"자동 진행 후 단계: "
        f"{auto_turn_game.state.turn_phase}"
    )

    print(
        f"자동 진행 후 게임 상태: "
        f"{auto_turn_game.state.status}"
    )


    print()
    print("=== 초보 AI 패 보호 버리기 테스트 ===")

    smart_beginner_game = create_test_game(
        game_id="TEST-BEGINNER-PROTECT",
        owner_id="TEST-USER",
        human_nickname="패 보호 테스트",
    )

    ai_player = (
        smart_beginner_game.state.players[1]
    )

    ai_player.hand = make_test_cards(
        [3, 3, 3, 11, 11, 9]
    )

    before_months = [
        card.month
        for card in ai_player.hand
    ]

    selected_card = choose_beginner_discard(
        ai_player
    )

    print(
        f"AI 손패: "
        f"{before_months}"
    )

    print(
        f"선택한 버림패: "
        f"{selected_card.month}월"
    )

    print(
        f"선택 후 실제 손패 수: "
        f"{len(ai_player.hand)}장"
    )


    print()
    print("=== 바가지 규칙 수정 테스트 완료 ===")
    print(
        "일반 바가지 2장 동일월 / "
        "폭탄 바가지 정확한 3+2 / "
        "패 변경 자동 해제 / 재선언 테스트를 포함합니다."
    )


    print()
    print("=== 초보 AI 바가지 선언 테스트 ===")

    ai_bagaji_game = create_test_game(
        game_id="TEST-AI-BAGAJI",
        owner_id="TEST-USER",
        human_nickname="AI 바가지 테스트",
    )

    ai_bagaji_engine = GameEngine(
        ai_bagaji_game.state
    )

    ai_player = (
        ai_bagaji_game.state.players[1]
    )

    # ---------------------------------
    # 일반 바가지
    # ---------------------------------

    ai_player.bbung_count = 1

    ai_player.hand = make_test_cards(
        [4, 4]
    )

    general_declared = (
        ai_bagaji_engine.try_beginner_ai_bagaji(
            ai_player.player_id
        )
    )

    general_months = [
        declaration.month
        for declaration
        in ai_bagaji_game.state.active_bagaji_declarations
    ]

    print(
        f"일반 바가지 선언 실행: "
        f"{general_declared}"
    )

    print(
        f"활성 일반 바가지: "
        f"{general_months}"
    )

    # ---------------------------------
    # 폭탄 바가지
    # ---------------------------------

    ai_bagaji_game.state.active_bagaji_declarations.clear()

    ai_player.bbung_count = 0

    ai_player.hand = make_test_cards(
        [3, 3, 3, 7, 7]
    )

    bomb_declared = (
        ai_bagaji_engine.try_beginner_ai_bagaji(
            ai_player.player_id
        )
    )

    bomb_months = [
        declaration.month
        for declaration
        in ai_bagaji_game.state.active_bomb_bagaji_declarations
    ]

    print(
        f"폭탄 바가지 선언 실행: "
        f"{bomb_declared}"
    )

    print(
        f"활성 폭탄 바가지 대상 월: "
        f"{bomb_months}"
    )


    print()
    print("=== 초보 AI 뻥 후 일반 바가지 자동 선언 테스트 ===")

    ai_bbung_bagaji_game = create_test_game(
        game_id="TEST-AI-BBUNG-BAGAJI",
        owner_id="TEST-USER",
        human_nickname="AI 뻥 바가지 테스트",
    )

    ai_bbung_bagaji_engine = GameEngine(
        ai_bbung_bagaji_game.state
    )

    p1 = ai_bbung_bagaji_game.state.players[0]
    p2 = ai_bbung_bagaji_game.state.players[1]
    p3 = ai_bbung_bagaji_game.state.players[2]

    # P1은 3월을 버린다.
    p1.hand = make_test_cards(
        [3, 5, 6, 7, 8, 10]
    )

    # P2 초보 AI:
    # 3월 2장으로 뻥
    # 9월을 추가로 버리면
    # 최종 손패가 [4, 4]
    p2.hand = make_test_cards(
        [3, 3, 4, 4, 9]
    )

    # P3은 추가 버림 9월에
    # 뻥할 수 없도록 구성
    p3.hand = make_test_cards(
        [1, 2, 5, 7, 11]
    )

    p1_three = next(
        card
        for card in p1.hand
        if card.month == 3
    )

    ai_bbung_bagaji_engine.discard_card(
        p1_three.card_id
    )

    ai_bbung_result = (
        ai_bbung_bagaji_engine
        .try_beginner_ai_bbung(
            p2.player_id
        )
    )

    p2_months_after_bbung = [
        card.month
        for card in p2.hand
    ]

    p2_general_bagaji_months = [
        declaration.month
        for declaration
        in ai_bbung_bagaji_game.state.active_bagaji_declarations
        if declaration.player_id == p2.player_id
    ]

    print(
        f"P2 뻥 실행: "
        f"{ai_bbung_result}"
    )

    print(
        f"P2 뻥 후 손패: "
        f"{p2_months_after_bbung}"
    )

    print(
        f"P2 뻥 횟수: "
        f"{p2.bbung_count}"
    )

    print(
        f"P2 활성 일반 바가지: "
        f"{p2_general_bagaji_months}"
    )


    print()
    print("=== 초보 AI 버리기 후 폭탄 바가지 자동 선언 테스트 ===")

    ai_bomb_flow_game = create_test_game(
        game_id="TEST-AI-BOMB-BAGAJI-FLOW",
        owner_id="TEST-USER",
        human_nickname="AI 폭탄 바가지 테스트",
    )

    ai_bomb_flow_engine = GameEngine(
        ai_bomb_flow_game.state
    )

    p1 = ai_bomb_flow_game.state.players[0]
    p2 = ai_bomb_flow_game.state.players[1]

    # 테스트에서는 P2가 현재 턴인 것으로 설정한다.
    ai_bomb_flow_game.state.current_turn_player_id = (
        p2.player_id
    )

    ai_bomb_flow_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    # P2는 6장을 가지고 있다.
    #
    # 3월 3장 = 폭탄
    # 7월 2장 = 바가지 대상
    # 12월 1장 = 초보 AI가 버릴 카드
    #
    # 초보 AI 버리기 전략상
    # 단독 카드인 12월을 먼저 버리게 된다.
    p2.hand = make_test_cards(
        [3, 3, 3, 7, 7, 12]
    )

    discarded_card = (
        ai_bomb_flow_engine
        .play_beginner_ai_discard(
            p2.player_id
        )
    )

    p2_months_after_discard = [
        card.month
        for card in p2.hand
    ]

    p2_bomb_bagaji_months = [
        declaration.month
        for declaration
        in ai_bomb_flow_game.state
        .active_bomb_bagaji_declarations
        if declaration.player_id == p2.player_id
    ]

    p2_bomb_months = [
        declaration.bomb_month
        for declaration
        in ai_bomb_flow_game.state
        .active_bomb_bagaji_declarations
        if declaration.player_id == p2.player_id
    ]

    print(
        f"P2가 버린 카드: "
        f"{discarded_card.month}월"
    )

    print(
        f"P2 버린 후 손패: "
        f"{p2_months_after_discard}"
    )

    print(
        f"P2 폭탄 월: "
        f"{p2_bomb_months}"
    )

    print(
        f"P2 활성 폭탄 바가지: "
        f"{p2_bomb_bagaji_months}"
    )


    print()
    print("=== 초보 AI 일반 바가지 실제 발동 통합 테스트 ===")

    ai_bagaji_trigger_game = create_test_game(
        game_id="TEST-AI-BAGAJI-TRIGGER",
        owner_id="TEST-USER",
        human_nickname="AI 바가지 발동 테스트",
    )

    ai_bagaji_trigger_engine = GameEngine(
        ai_bagaji_trigger_game.state
    )

    p1 = ai_bagaji_trigger_game.state.players[0]
    p2 = ai_bagaji_trigger_game.state.players[1]
    p3 = ai_bagaji_trigger_game.state.players[2]

    # --------------------------------------------------
    # 1. P2 초보 AI가 먼저 뻥해서
    #    최종 손패 [4, 4]를 만든다.
    # --------------------------------------------------

    p1.hand = make_test_cards(
        [3, 5, 6, 7, 8, 10]
    )

    p2.hand = make_test_cards(
        [3, 3, 4, 4, 9]
    )

    p3.hand = make_test_cards(
        [1, 2, 5, 7, 11]
    )

    ai_bagaji_trigger_game.state.current_turn_player_id = (
        p1.player_id
    )

    ai_bagaji_trigger_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    p1_three = next(
        card
        for card in p1.hand
        if card.month == 3
    )

    ai_bagaji_trigger_engine.discard_card(
        p1_three.card_id
    )

    ai_bagaji_trigger_engine.try_beginner_ai_bbung(
        p2.player_id
    )

    p2_hand_after_bbung = [
        card.month
        for card in p2.hand
    ]

    active_general_months = [
        declaration.month
        for declaration
        in ai_bagaji_trigger_game.state.active_bagaji_declarations
        if declaration.player_id == p2.player_id
    ]

    print(
        f"P2 뻥 후 손패: "
        f"{p2_hand_after_bbung}"
    )

    print(
        f"P2 활성 일반 바가지: "
        f"{active_general_months}"
    )

    # --------------------------------------------------
    # 2. 이후 P3가 4월을 버리면
    #    P2의 일반 바가지가 실제 발동해야 한다.
    # --------------------------------------------------

    ai_bagaji_trigger_game.state.current_turn_player_id = (
        p3.player_id
    )

    ai_bagaji_trigger_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    p3.hand = make_test_cards(
        [4, 1, 2, 5, 7, 11]
    )

    p3_four = next(
        card
        for card in p3.hand
        if card.month == 4
    )

    ai_bagaji_trigger_engine.discard_card(
        p3_four.card_id
    )

    print(
        f"라운드 상태: "
        f"{ai_bagaji_trigger_game.state.status}"
    )

    print(
        f"라운드 종료 이유: "
        f"{ai_bagaji_trigger_game.state.round_end_reason}"
    )

    print(
        f"바가지 승자: "
        f"{ai_bagaji_trigger_game.state.round_winner_id}"
    )

    print(
        f"바가지 피해자: "
        f"{ai_bagaji_trigger_game.state.bagaji_victim_id}"
    )

    print(
        f"발동 월: "
        f"{ai_bagaji_trigger_game.state.triggered_bagaji_month}"
    )

    print("플레이어별 점수:")

    for player in ai_bagaji_trigger_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )


    print()
    print("=== 초보 AI 폭탄 바가지 실제 발동 통합 테스트 ===")

    ai_bomb_trigger_game = create_test_game(
        game_id="TEST-AI-BOMB-BAGAJI-TRIGGER",
        owner_id="TEST-USER",
        human_nickname="AI 폭탄 바가지 발동 테스트",
    )

    ai_bomb_trigger_engine = GameEngine(
        ai_bomb_trigger_game.state
    )

    p1 = ai_bomb_trigger_game.state.players[0]
    p2 = ai_bomb_trigger_game.state.players[1]
    p3 = ai_bomb_trigger_game.state.players[2]

    # --------------------------------------------------
    # 1. P2 초보 AI가 12월을 버리고
    #    [3,3,3,7,7] 상태가 되면서
    #    7월 폭탄 바가지를 자동 선언한다.
    # --------------------------------------------------

    p2.hand = make_test_cards(
        [3, 3, 3, 7, 7, 12]
    )

    ai_bomb_trigger_game.state.current_turn_player_id = (
        p2.player_id
    )

    ai_bomb_trigger_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    discarded_card = (
        ai_bomb_trigger_engine
        .play_beginner_ai_discard(
            p2.player_id
        )
    )

    p2_hand_after_discard = [
        card.month
        for card in p2.hand
    ]

    active_bomb_months = [
        declaration.month
        for declaration
        in ai_bomb_trigger_game.state
        .active_bomb_bagaji_declarations
        if declaration.player_id == p2.player_id
    ]

    active_bomb_source_months = [
        declaration.bomb_month
        for declaration
        in ai_bomb_trigger_game.state
        .active_bomb_bagaji_declarations
        if declaration.player_id == p2.player_id
    ]

    print(
        f"P2가 버린 카드: "
        f"{discarded_card.month}월"
    )

    print(
        f"P2 버린 후 손패: "
        f"{p2_hand_after_discard}"
    )

    print(
        f"P2 폭탄 월: "
        f"{active_bomb_source_months}"
    )

    print(
        f"P2 활성 폭탄 바가지: "
        f"{active_bomb_months}"
    )

    # --------------------------------------------------
    # 2. 이후 P3가 7월을 버리면
    #    P2의 폭탄 바가지가 실제 발동해야 한다.
    # --------------------------------------------------

    p3.hand = make_test_cards(
        [7, 1, 2, 5, 8, 11]
    )

    ai_bomb_trigger_game.state.current_turn_player_id = (
        p3.player_id
    )

    ai_bomb_trigger_game.state.turn_phase = (
        TurnPhase.DISCARD
    )

    p3_seven = next(
        card
        for card in p3.hand
        if card.month == 7
    )

    ai_bomb_trigger_engine.discard_card(
        p3_seven.card_id
    )

    print(
        f"라운드 상태: "
        f"{ai_bomb_trigger_game.state.status}"
    )

    print(
        f"라운드 종료 이유: "
        f"{ai_bomb_trigger_game.state.round_end_reason}"
    )

    print(
        f"폭탄 바가지 승자: "
        f"{ai_bomb_trigger_game.state.round_winner_id}"
    )

    print(
        f"폭탄 바가지 피해자: "
        f"{ai_bomb_trigger_game.state.bagaji_victim_id}"
    )

    print(
        f"발동 월: "
        f"{ai_bomb_trigger_game.state.triggered_bagaji_month}"
    )

    print("플레이어별 점수:")

    for player in ai_bomb_trigger_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )


    print()
    print("=== 초보 AI 기습 STOP 자동 선언 통합 테스트 ===")

    ai_surprise_game = create_test_game(
        game_id="TEST-AI-SURPRISE-STOP",
        owner_id="TEST-USER",
        human_nickname="AI 기습 STOP 테스트",
    )

    ai_surprise_engine = GameEngine(
        ai_surprise_game.state
    )

    p1 = ai_surprise_game.state.players[0]
    p2 = ai_surprise_game.state.players[1]
    p3 = ai_surprise_game.state.players[2]

    # P2가 현재 초보 AI 턴이라고 가정한다.
    ai_surprise_game.state.current_turn_player_id = (
        p2.player_id
    )

    ai_surprise_game.state.turn_phase = (
        TurnPhase.DRAW
    )

    # P2:
    # 손패 2장
    # 합계 2 + 3 = 5
    # 본인도 뻥 이력 있음
    p2.hand = make_test_cards(
        [2, 3]
    )

    p2.bbung_count = 1

    # 3인 게임에서는 본인 포함
    # 2명 이상이 뻥한 상태여야 한다.
    p1.bbung_count = 1
    p3.bbung_count = 0

    # 독박 판정을 확인하기 위한 다른 플레이어 손패
    p1.hand = make_test_cards(
        [4, 5, 6]
    )

    # P3의 현재 손패 점수는 3점.
    # 기습 STOP 선언자인 P2의 기본 점수 5보다 낮으므로
    # 독박 조건이 성립해야 한다.
    p3.hand = make_test_cards(
        [1, 2]
    )

    ai_surprise_engine.play_beginner_ai_turn(
        p2.player_id
    )

    print(
        f"라운드 상태: "
        f"{ai_surprise_game.state.status}"
    )

    print(
        f"라운드 종료 이유: "
        f"{ai_surprise_game.state.round_end_reason}"
    )

    print(
        f"기습 STOP 승자: "
        f"{ai_surprise_game.state.round_winner_id}"
    )

    print(
        f"독박 여부: "
        f"{ai_surprise_game.state.surprise_stop_dokbak}"
    )

    print(
        f"P2 라운드 점수: "
        f"{p2.round_score}"
    )

    print("플레이어별 점수:")

    for player in ai_surprise_game.state.players:
        print(
            f"  {player.nickname}: "
            f"{player.round_score}점"
        )


if __name__ == "__main__":
    main()