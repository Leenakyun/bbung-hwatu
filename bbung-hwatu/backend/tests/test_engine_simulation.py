import unittest
from unittest.mock import patch

from game.deck import Deck
from game.engine import GameEngine
from game.models import (
    AIDifficulty,
    Card,
    Player,
    PlayerType,
)
from game.ai.advanced import (
    choose_advanced_stop,
    choose_advanced_bbung_cards,
    choose_advanced_general_bagaji_month,
    choose_advanced_bomb_bagaji_month,
    should_advanced_declare_surprise_stop,
)
from game.ai.tazza import (
    choose_tazza_discard,
    choose_tazza_stop,
    choose_tazza_bbung_cards,
    choose_tazza_general_bagaji_month,
    choose_tazza_bomb_bagaji_month,
    should_tazza_declare_surprise_stop,
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
    TurnPhase,
)


def create_bot_game(
    game_id: str,
    difficulty: AIDifficulty,
):
    players = [
        Player(
            player_id=f"{game_id}-P{i}",
            nickname=f"AI {i}",
            player_type=PlayerType.BOT,
            ai_difficulty=difficulty,
        )
        for i in range(1, 4)
    ]

    state = GameState(
        game_id=game_id,
        players=players,
    )

    state.dealer_id = players[0].player_id
    state.current_turn_player_id = (
        players[0].player_id
    )

    state.deck = Deck()
    state.deck.shuffle()

    deal_initial_cards(
        deck=state.deck,
        players=state.players,
        dealer_id=state.dealer_id,
    )

    state.status = GameStatus.PLAYING
    state.turn_phase = TurnPhase.DISCARD
    state.round_winner_decided_by_tie_break = (
        False
    )

    return state, GameEngine(state)


class EngineSimulationTests(
    unittest.TestCase
):
    def run_games(
        self,
        difficulty: AIDifficulty,
        game_count: int = 20,
    ):
        for game_index in range(
            1,
            game_count + 1,
        ):
            state, engine = create_bot_game(
                game_id=(
                    f"SIM-"
                    f"{difficulty.value}-"
                    f"{game_index:03d}"
                ),
                difficulty=difficulty,
            )

            safety = 0

            while (
                state.status
                != GameStatus.GAME_END
            ):
                safety += 1

                self.assertLess(
                    safety,
                    500,
                    "게임 진행이 멈췄습니다.",
                )

                if (
                    state.status
                    == GameStatus.PLAYING
                ):
                    engine.run_beginner_ai_until_human_turn()

                    self.assertNotEqual(
                        state.status,
                        GameStatus.PLAYING,
                        (
                            "전원 AI 게임인데 "
                            "자동 진행이 중간에 멈췄습니다."
                        ),
                    )

                    continue

                if (
                    state.status
                    == GameStatus.ROUND_END
                ):
                    winner_id = (
                        state.round_winner_id
                    )
                    old_round = (
                        state.round_number
                    )

                    self.assertIsNotNone(
                        winner_id,
                        (
                            f"{old_round}라운드 "
                            "승자가 없습니다."
                        ),
                    )

                    engine.continue_after_round()

                    if (
                        state.status
                        == GameStatus.PLAYING
                    ):
                        self.assertEqual(
                            state.dealer_id,
                            winner_id,
                            (
                                "직전 라운드 승자가 "
                                "다음 선이 아닙니다."
                            ),
                        )

                    continue

                if (
                    state.status
                    == GameStatus.TIE_BREAK
                ):
                    player_id = (
                        engine
                        .get_current_tie_break_player_id()
                    )

                    engine.draw_tie_break_card(
                        player_id
                    )

                    continue

                self.fail(
                    f"예상하지 못한 상태: "
                    f"{state.status}"
                )

            self.assertIsNotNone(
                state.game_winner_id
            )

    def test_beginner_20_games(self):
        self.run_games(
            AIDifficulty.BEGINNER
        )

    def test_intermediate_20_games(self):
        self.run_games(
            AIDifficulty.INTERMEDIATE
        )

    def test_advanced_20_games(self):
        self.run_games(
            AIDifficulty.ADVANCED
        )

    def test_tazza_20_games(self):
        self.run_games(
            AIDifficulty.TAZZA
        )

    def test_advanced_stop_chooses_best_score(self):
        player = Player(
            player_id="ADV-STOP",
            nickname="고수",
            player_type=PlayerType.BOT,
            ai_difficulty=(
                AIDifficulty.ADVANCED
            ),
            hand=[
                Card(1, 1),
                Card(1, 2),
                Card(1, 3),
                Card(1, 4),
                Card(2, 1),
                Card(2, 2),
            ],
        )

        available = get_available_stops(
            player.hand
        )

        self.assertIn(
            StopType.MINUS_100,
            available,
        )
        self.assertIn(
            StopType.MINUS_200,
            available,
        )

        selected = choose_advanced_stop(
            player,
            available,
            calculate_stop_score,
        )

        self.assertEqual(
            selected,
            StopType.MINUS_200,
        )

    def test_advanced_bbung_preserves_better_hand(self):
        player = Player(
            player_id="ADV-BBUNG",
            nickname="고수",
            player_type=PlayerType.BOT,
            ai_difficulty=(
                AIDifficulty.ADVANCED
            ),
            hand=[
                Card(3, 1),
                Card(3, 2),
                Card(5, 1),
                Card(5, 2),
                Card(9, 1),
                Card(12, 1),
            ],
        )

        selection = (
            choose_advanced_bbung_cards(
                player=player,
                discarded_card=Card(
                    3,
                    3,
                ),
                discard_pile=[],
            )
        )

        self.assertIsNotNone(
            selection
        )

        matching_cards, extra_card = (
            selection
        )

        self.assertEqual(
            {
                card.month
                for card in matching_cards
            },
            {3},
        )

        # 5월 페어는 보존하고
        # 단독 고월 카드를 우선 정리해야 한다.
        self.assertEqual(
            extra_card.month,
            12,
        )


    def test_advanced_general_bagaji_skips_dead_month(self):
        player = Player(
            player_id="ADV-BAGAJI",
            nickname="고수",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.ADVANCED,
            hand=[
                Card(5, 1),
                Card(5, 2),
            ],
            bbung_count=1,
        )

        # 나머지 5월 두 장이 모두 이미 공개됨:
        # 상대가 5월을 버릴 가능성이 0이므로 선언하지 않는다.
        dead_discard_pile = [
            Card(5, 3),
            Card(5, 4),
        ]

        self.assertIsNone(
            choose_advanced_general_bagaji_month(
                player,
                dead_discard_pile,
            )
        )

        # 아직 한 장이라도 미공개면 선언 후보.
        live_discard_pile = [
            Card(5, 3),
        ]

        self.assertEqual(
            choose_advanced_general_bagaji_month(
                player,
                live_discard_pile,
            ),
            5,
        )

    def test_advanced_bomb_bagaji_skips_dead_month(self):
        player = Player(
            player_id="ADV-BOMB-BAGAJI",
            nickname="고수",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.ADVANCED,
            hand=[
                Card(3, 1),
                Card(3, 2),
                Card(3, 3),
                Card(7, 1),
                Card(7, 2),
            ],
        )

        dead_discard_pile = [
            Card(7, 3),
            Card(7, 4),
        ]

        self.assertIsNone(
            choose_advanced_bomb_bagaji_month(
                player,
                dead_discard_pile,
            )
        )

        self.assertEqual(
            choose_advanced_bomb_bagaji_month(
                player,
                [Card(7, 3)],
            ),
            7,
        )

    def test_advanced_surprise_stop_is_risk_aware(self):
        safe_player = Player(
            player_id="ADV-SURPRISE-SAFE",
            nickname="고수",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.ADVANCED,
            hand=[
                Card(1, 1),
                Card(2, 1),
            ],
        )

        self.assertTrue(
            should_advanced_declare_surprise_stop(
                safe_player,
                [],
            )
        )

        cautious_player = Player(
            player_id="ADV-SURPRISE-CAUTIOUS",
            nickname="고수",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.ADVANCED,
            hand=[
                Card(2, 1),
                Card(2, 2),
            ],
        )

        self.assertFalse(
            should_advanced_declare_surprise_stop(
                cautious_player,
                [],
            )
        )

        # 저월 카드가 충분히 공개되어 있으면
        # 4점 기습 STOP도 감수한다.
        visible_low_cards = [
            Card(1, 1),
            Card(1, 2),
            Card(1, 3),
        ]

        self.assertTrue(
            should_advanced_declare_surprise_stop(
                cautious_player,
                visible_low_cards,
            )
        )


    def test_tazza_discard_uses_expected_value(self):
        player = Player(
            player_id="TAZZA-TEST",
            nickname="타짜",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            hand=[
                Card(1, 1),
                Card(2, 1),
                Card(3, 1),
                Card(4, 1),
                Card(5, 1),
                Card(12, 1),
            ],
        )

        selected = choose_tazza_discard(
            player,
            [],
        )

        self.assertEqual(
            selected.month,
            12,
        )

    def test_tazza_can_delay_zero_stop(self):
        player = Player(
            player_id="TAZZA-STOP",
            nickname="타짜",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            total_score=20,
            hand=[
                Card(2, 1),
                Card(2, 2),
                Card(5, 1),
                Card(5, 2),
                Card(9, 1),
                Card(9, 2),
            ],
        )

        leader = Player(
            player_id="LEADER",
            nickname="선두",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.ADVANCED,
            total_score=-30,
        )

        available = get_available_stops(
            player.hand
        )

        selected = choose_tazza_stop(
            player,
            available,
            calculate_stop_score,
            5,
            [player, leader],
        )

        self.assertIsNone(
            selected
        )

    def test_tazza_takes_negative_stop(self):
        player = Player(
            player_id="TAZZA-NEG",
            nickname="타짜",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            total_score=20,
            hand=[
                Card(10, 1),
                Card(10, 2),
                Card(10, 3),
                Card(10, 4),
                Card(11, 1),
                Card(11, 2),
            ],
        )

        available = get_available_stops(
            player.hand
        )

        selected = choose_tazza_stop(
            player,
            available,
            calculate_stop_score,
            5,
            [player],
        )

        self.assertIsNotNone(
            selected
        )
        self.assertLess(
            calculate_stop_score(
                player.hand,
                selected,
            ),
            0,
        )

    def test_tazza_bbung_can_decline(self):
        player = Player(
            player_id="TAZZA-BBUNG",
            nickname="타짜",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            hand=[
                Card(1, 1),
                Card(1, 2),
                Card(2, 1),
                Card(3, 1),
                Card(4, 1),
                Card(5, 1),
            ],
        )

        # 1월 두 장을 뻥에 쓰면 연속월 진행도가 크게 무너지는 패.
        result = choose_tazza_bbung_cards(
            player,
            Card(1, 3),
            [],
        )

        self.assertIsNone(
            result
        )

    def test_tazza_general_bagaji_is_score_aware(self):
        player = Player(
            player_id="TAZZA-BAGAJI",
            nickname="타짜",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            total_score=-30,
            bbung_count=1,
            hand=[
                Card(5, 1),
                Card(5, 2),
            ],
        )

        other = Player(
            player_id="OTHER",
            nickname="상대",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.ADVANCED,
            total_score=10,
        )

        # 미공개 5월이 한 장뿐인 초중반 선두:
        # 발동 확률이 낮으므로 선언 보류.
        self.assertIsNone(
            choose_tazza_general_bagaji_month(
                player,
                [Card(5, 3)],
                5,
                [player, other],
            )
        )

        # 후반에는 같은 상황도 선언.
        self.assertEqual(
            choose_tazza_general_bagaji_month(
                player,
                [Card(5, 3)],
                16,
                [player, other],
            ),
            5,
        )

    def test_tazza_bomb_bagaji_takes_live_target(self):
        player = Player(
            player_id="TAZZA-BOMB",
            nickname="타짜",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            hand=[
                Card(3, 1),
                Card(3, 2),
                Card(3, 3),
                Card(7, 1),
                Card(7, 2),
            ],
        )

        self.assertEqual(
            choose_tazza_bomb_bagaji_month(
                player,
                [Card(7, 3)],
                4,
                [player],
            ),
            7,
        )

        self.assertIsNone(
            choose_tazza_bomb_bagaji_month(
                player,
                [
                    Card(7, 3),
                    Card(7, 4),
                ],
                4,
                [player],
            )
        )


    def test_three_player_first_deck_exhaustion_ends_round(self):
        players = [
            Player(
                player_id=f"P{i}",
                nickname=f"P{i}",
                player_type=PlayerType.HUMAN,
            )
            for i in range(1, 4)
        ]

        players[0].hand = [
            Card(1, 1),
            Card(2, 1),
        ]
        players[1].hand = [
            Card(4, 1),
            Card(5, 1),
        ]
        players[2].hand = [
            Card(7, 1),
            Card(8, 1),
        ]

        state = GameState(
            game_id="THREE-PHASE1-END",
            players=players,
        )
        state.status = GameStatus.PLAYING
        state.current_turn_player_id = "P1"
        state.turn_phase = TurnPhase.DRAW
        state.deck = Deck()
        state.deck.cards = []
        state.discard_pile = [
            Card(9, 1),
            Card(10, 1),
        ]

        engine = GameEngine(
            state
        )

        can_continue = (
            engine.handle_empty_deck()
        )

        self.assertFalse(
            can_continue
        )
        self.assertEqual(
            state.status,
            GameStatus.ROUND_END,
        )
        self.assertEqual(
            state.round_winner_id,
            "P1",
        )
        self.assertFalse(
            state.deck_reshuffle_used
        )

    def test_four_player_first_deck_exhaustion_ends_round(self):
        players = [
            Player(
                player_id=f"P{i}",
                nickname=f"P{i}",
                player_type=PlayerType.HUMAN,
            )
            for i in range(1, 5)
        ]

        hands = [
            [Card(8, 1), Card(9, 1)],
            [Card(1, 1), Card(2, 1)],  # 승자
            [Card(5, 1), Card(6, 1)],
            [Card(10, 1), Card(11, 1)],
        ]

        for player, hand in zip(
            players,
            hands,
        ):
            player.hand = hand

        state = GameState(
            game_id="FOUR-PHASE1-END",
            players=players,
        )
        state.status = GameStatus.PLAYING
        state.current_turn_player_id = "P1"
        state.turn_phase = TurnPhase.DRAW
        state.deck = Deck()
        state.deck.cards = []
        state.discard_pile = [
            Card(12, 1),
        ]

        engine = GameEngine(
            state
        )

        self.assertFalse(
            engine.handle_empty_deck()
        )
        self.assertEqual(
            state.round_winner_id,
            "P2",
        )
        self.assertFalse(
            state.deck_reshuffle_used
        )

    def test_five_player_first_exhaustion_starts_phase_two(self):
        players = [
            Player(
                player_id=f"P{i}",
                nickname=f"P{i}",
                player_type=PlayerType.HUMAN,
            )
            for i in range(1, 6)
        ]

        state = GameState(
            game_id="FIVE-PHASE2",
            players=players,
        )
        state.status = GameStatus.PLAYING
        state.current_turn_player_id = "P3"
        state.turn_phase = TurnPhase.DRAW
        state.deck = Deck()
        state.deck.cards = []
        state.discard_pile = [
            Card(1, 1),
            Card(2, 1),
            Card(3, 1),
        ]
        state.last_discarded_by_player_id = "P3"
        state.last_discarded_card = Card(
            3,
            1,
        )

        engine = GameEngine(
            state
        )

        can_continue = (
            engine.handle_empty_deck()
        )

        self.assertTrue(
            can_continue
        )
        self.assertEqual(
            state.status,
            GameStatus.PLAYING,
        )
        self.assertTrue(
            state.deck_reshuffle_used
        )
        self.assertEqual(
            len(state.deck.cards),
            3,
        )
        self.assertEqual(
            state.discard_pile,
            [],
        )
        self.assertEqual(
            state.current_turn_player_id,
            "P4",
        )
        self.assertEqual(
            state.turn_phase,
            TurnPhase.DRAW,
        )

    def test_six_player_second_exhaustion_lowest_score_wins(self):
        players = [
            Player(
                player_id=f"P{i}",
                nickname=f"P{i}",
                player_type=PlayerType.HUMAN,
            )
            for i in range(1, 7)
        ]

        hands = [
            [Card(10, 1), Card(10, 2)],
            [Card(8, 1), Card(9, 1)],
            [Card(6, 1), Card(7, 1)],
            [Card(4, 1), Card(5, 1)],
            [Card(2, 1), Card(3, 1)],
            [Card(1, 1), Card(2, 2)],  # 승자
        ]

        for player, hand in zip(
            players,
            hands,
        ):
            player.hand = hand

        state = GameState(
            game_id="SIX-PHASE2-END",
            players=players,
        )
        state.status = GameStatus.PLAYING
        state.current_turn_player_id = "P1"
        state.turn_phase = TurnPhase.DRAW
        state.deck = Deck()
        state.deck.cards = []
        state.deck_reshuffle_used = True

        engine = GameEngine(
            state
        )

        can_continue = (
            engine.handle_empty_deck()
        )

        self.assertFalse(
            can_continue
        )
        self.assertEqual(
            state.status,
            GameStatus.ROUND_END,
        )
        self.assertEqual(
            state.round_winner_id,
            "P6",
        )
        self.assertTrue(
            state.deck_reshuffle_used
        )

    def test_five_player_second_exhaustion_tie_uses_three_card_tiebreak(self):
        players = [
            Player(
                player_id=f"P{i}",
                nickname=f"P{i}",
                player_type=PlayerType.HUMAN,
            )
            for i in range(1, 6)
        ]

        players[0].hand = [
            Card(1, 1),
            Card(2, 1),
        ]
        players[1].hand = [
            Card(1, 2),
            Card(2, 2),
        ]
        players[2].hand = [
            Card(5, 1),
            Card(6, 1),
        ]
        players[3].hand = [
            Card(7, 1),
            Card(8, 1),
        ]
        players[4].hand = [
            Card(9, 1),
            Card(10, 1),
        ]

        state = GameState(
            game_id="FIVE-PHASE2-TIE",
            players=players,
        )
        state.status = GameStatus.PLAYING
        state.current_turn_player_id = "P1"
        state.turn_phase = TurnPhase.DRAW
        state.deck = Deck()
        state.deck.cards = []
        state.deck_reshuffle_used = True

        engine = GameEngine(
            state
        )

        with patch.object(
            engine,
            "_resolve_round_three_card_tie",
            return_value="P2",
        ) as mocked:
            engine.handle_empty_deck()

        mocked.assert_called_once_with(
            ["P1", "P2"]
        )
        self.assertEqual(
            state.round_winner_id,
            "P2",
        )
        self.assertTrue(
            state.round_winner_decided_by_tie_break
        )

    def test_general_bagaji_auto_cancels_when_pair_breaks(self):
        player = Player(
            player_id="P1",
            nickname="P1",
            player_type=PlayerType.HUMAN,
            hand=[
                Card(5, 1),
                Card(5, 2),
            ],
            bbung_count=1,
        )

        other = Player(
            player_id="P2",
            nickname="P2",
            player_type=PlayerType.HUMAN,
            hand=[
                Card(9, 1),
                Card(10, 1),
                Card(11, 1),
            ],
        )

        state = GameState(
            game_id="BAGAJI-CANCEL",
            players=[
                player,
                other,
            ],
        )
        state.status = GameStatus.PLAYING
        state.current_turn_player_id = "P1"
        state.turn_phase = TurnPhase.DISCARD

        engine = GameEngine(
            state
        )

        engine.declare_general_bagaji(
            player_id="P1",
            month=5,
        )

        self.assertEqual(
            len(
                state.active_bagaji_declarations
            ),
            1,
        )

        # 바가지 선언 뒤 다른 월 카드를 드로우한 상황.
        # 대상 5월 페어 자체는 아직 유지되므로 선언도 유지된다.
        player.hand.append(
            Card(8, 1)
        )

        engine.refresh_active_bagaji_declarations()

        self.assertEqual(
            len(
                state.active_bagaji_declarations
            ),
            1,
        )

        # 선언 근거였던 5월 두 장 중 한 장을 버리면
        # 대상 페어가 깨지므로 즉시 자동 철회되어야 한다.
        engine.discard_card(
            "05-01"
        )

        self.assertEqual(
            state.active_bagaji_declarations,
            [],
        )

    def test_bomb_bagaji_auto_cancels_when_target_pair_breaks(self):
        player = Player(
            player_id="P1",
            nickname="P1",
            player_type=PlayerType.HUMAN,
            hand=[
                Card(3, 1),
                Card(3, 2),
                Card(3, 3),
                Card(7, 1),
                Card(7, 2),
            ],
        )

        other = Player(
            player_id="P2",
            nickname="P2",
            player_type=PlayerType.HUMAN,
            hand=[
                Card(9, 1),
                Card(10, 1),
                Card(11, 1),
            ],
        )

        state = GameState(
            game_id="BOMB-BAGAJI-CANCEL",
            players=[
                player,
                other,
            ],
        )
        state.status = GameStatus.PLAYING
        state.current_turn_player_id = "P1"
        state.turn_phase = TurnPhase.DISCARD

        engine = GameEngine(
            state
        )

        engine.declare_bomb_bagaji(
            player_id="P1",
            month=7,
        )

        self.assertEqual(
            len(
                state.active_bomb_bagaji_declarations
            ),
            1,
        )

        # 폭탄 바가지의 대상 페어인 7월 중 한 장을 버리면
        # 선언이 자동 철회되어야 한다.
        engine.discard_card(
            "07-01"
        )

        self.assertEqual(
            state.active_bomb_bagaji_declarations,
            [],
        )


    def test_tazza_surprise_stop_uses_round_and_score(self):
        leader = Player(
            player_id="TAZZA-SURPRISE",
            nickname="타짜",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            total_score=-20,
            hand=[
                Card(1, 1),
                Card(2, 1),
            ],
        )

        follower = Player(
            player_id="FOLLOWER",
            nickname="추격자",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.ADVANCED,
            total_score=10,
        )

        # 합 3 + 누적 선두 -> 초반에도 선언 가능
        self.assertTrue(
            should_tazza_declare_surprise_stop(
                leader,
                [],
                5,
                [leader, follower],
            )
        )

        cautious = Player(
            player_id="TAZZA-CAUTIOUS",
            nickname="타짜2",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            total_score=20,
            hand=[
                Card(2, 1),
                Card(2, 2),
            ],
        )

        # 합 4, 선두 아님, 초반 -> 보류
        self.assertFalse(
            should_tazza_declare_surprise_stop(
                cautious,
                [],
                5,
                [cautious, leader],
            )
        )

        # 후반 + 선두 + 저월 공개량 충분 -> 선언
        late_leader = Player(
            player_id="TAZZA-LATE",
            nickname="타짜3",
            player_type=PlayerType.BOT,
            ai_difficulty=AIDifficulty.TAZZA,
            total_score=-50,
            hand=[
                Card(2, 1),
                Card(2, 2),
            ],
        )

        visible_low = [
            Card(1, 1),
            Card(1, 2),
            Card(1, 3),
        ]

        self.assertTrue(
            should_tazza_declare_surprise_stop(
                late_leader,
                visible_low,
                16,
                [late_leader, follower],
            )
        )

if __name__ == "__main__":
    unittest.main()
