import unittest
import time
from unittest.mock import patch

import app as app_module
from game.models import Card
from game.state import GameStatus


class OnlineRoomFlowTests(
    unittest.TestCase
):
    def setUp(self):
        app_module.app.config.update(
            TESTING=True
        )

        for game_id in list(
            app_module.bbung_timers
        ):
            app_module.cancel_online_bbung_timer(
                game_id
            )

        app_module.manager.games.clear()
        app_module.auth_store.clear_for_tests()

        self.client = (
            app_module.app.test_client()
        )

        self.client.post(
            "/api/auth/register",
            json={
                "username": "owner",
                "password": "secret1",
                "nickname": "방장",
            },
        )

        login = self.client.post(
            "/api/auth/login",
            json={
                "username": "owner",
                "password": "secret1",
            },
        ).get_json()

        self.auth_token = login[
            "token"
        ]

        self.client.environ_base[
            "HTTP_AUTHORIZATION"
        ] = (
            f"Bearer {self.auth_token}"
        )

    def tearDown(self):
        for game_id in list(
            app_module.bbung_timers
        ):
            app_module.cancel_online_bbung_timer(
                game_id
            )

    def create_solo_game(self):
        response = self.client.post(
            "/api/games",
            json={
                "owner_id": "SOLO-OWNER",
                "nickname": "솔로",
                "ai_difficulty": "BEGINNER",
            },
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        return response.get_json()

    def test_create_online_room_waiting(self):
        response = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 4,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["mode"],
            "ONLINE",
        )
        self.assertEqual(
            data["status"],
            "WAITING",
        )
        self.assertEqual(
            data["max_players"],
            4,
        )
        self.assertEqual(
            len(data["players"]),
            1,
        )
        self.assertEqual(
            data["players"][0]["player_type"],
            "HUMAN",
        )

    def test_private_room_requires_valid_password(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "nickname": "방장",
                "max_players": 4,
                "is_private": True,
                "room_password": "1234",
            },
        )

        self.assertEqual(
            room.status_code,
            200,
        )

        room_data = room.get_json()
        game_id = room_data[
            "game_id"
        ]

        self.assertTrue(
            room_data[
                "is_private"
            ]
        )
        self.assertNotIn(
            "room_password",
            room_data,
        )
        self.assertNotIn(
            "room_password_hash",
            room_data,
        )

        rejected = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구",
                "client_id": "FRIEND-WRONG",
                "room_password": "9999",
            },
        )

        self.assertEqual(
            rejected.status_code,
            403,
        )
        self.assertEqual(
            rejected.get_json()[
                "error"
            ],
            "INVALID_ROOM_PASSWORD",
        )

        accepted = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구",
                "client_id": "FRIEND-RIGHT",
                "room_password": "1234",
            },
        )

        self.assertEqual(
            accepted.status_code,
            200,
        )
        self.assertEqual(
            len(
                accepted.get_json()[
                    "players"
                ]
            ),
            2,
        )

    def test_private_room_password_is_hashed(self):
        response = self.client.post(
            "/api/online/rooms",
            json={
                "nickname": "방장",
                "max_players": 3,
                "is_private": True,
                "room_password": "family-secret",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        game = app_module.manager.get_game(
            response.get_json()[
                "game_id"
            ]
        )

        self.assertIsNotNone(
            game.room_password_hash
        )
        self.assertNotEqual(
            game.room_password_hash,
            "family-secret",
        )

    def test_private_room_password_must_be_at_least_four_characters(self):
        response = self.client.post(
            "/api/online/rooms",
            json={
                "nickname": "방장",
                "max_players": 3,
                "is_private": True,
                "room_password": "123",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.get_json()[
                "error"
            ],
            "ROOM_PASSWORD_TOO_SHORT",
        )

    def test_join_online_room(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        response = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구1",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["mode"],
            "ONLINE",
        )
        self.assertEqual(
            len(data["players"]),
            2,
        )
        self.assertTrue(
            all(
                player["player_type"]
                == "HUMAN"
                for player in data["players"]
            )
        )

    def test_room_full(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            response = self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )
            self.assertEqual(
                response.status_code,
                200,
            )

        response = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "초과인원",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.get_json()["error"],
            "ROOM_FULL",
        )

    def test_solo_room_rejects_online_join(self):
        solo = self.create_solo_game()
        game_id = solo["game_id"]

        response = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "침입자",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.get_json()["error"],
            "GAME_MODE_MISMATCH",
        )

    def test_online_room_is_not_solo_game(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        viewer_id = (
            room["viewer_player_id"]
        )

        response = self.client.get(
            f"/api/online/rooms/{game_id}"
            f"?player_id={viewer_id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        data = response.get_json()

        self.assertEqual(
            data["mode"],
            "ONLINE",
        )
        self.assertEqual(
            data["deck_count"],
            0,
        )
        self.assertIsNone(
            data["turn_phase"]
        )


    def test_start_online_room_requires_at_least_three_players(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 6,
            },
        ).get_json()

        game_id = room["game_id"]

        # 방장 포함 2명뿐이면 시작 불가.
        self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구1",
            },
        )

        response = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "DAY",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.get_json()["error"],
            "NOT_ENOUGH_PLAYERS",
        )

    def test_owner_can_start_before_room_is_full(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 6,
            },
        ).get_json()

        game_id = room["game_id"]

        # 최대 정원은 6명이지만 현재 3명만 모은다.
        for nickname in (
            "친구1",
            "친구2",
        ):
            join_response = self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )
            self.assertEqual(
                join_response.status_code,
                200,
            )

        response = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "NIGHT",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.get_data(
                as_text=True
            ),
        )

        selection = response.get_json()

        self.assertEqual(
            selection["status"],
            "DEALER_SELECTION",
        )
        self.assertEqual(
            selection["max_players"],
            6,
        )
        self.assertEqual(
            len(selection["players"]),
            3,
        )
        self.assertTrue(
            selection[
                "dealer_selection_history"
            ]
        )

        confirm = self.client.post(
            f"/api/online/rooms/{game_id}"
            f"/confirm-start",
            json={
                "owner_id": "OWNER-1",
            },
        )

        self.assertEqual(
            confirm.status_code,
            200,
        )

        data = confirm.get_json()

        self.assertEqual(
            data["status"],
            "PLAYING",
        )
        self.assertEqual(
            data["deck_count"],
            32,
        )

    def test_only_owner_can_start_online_room(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )

        self.client.post(
            "/api/auth/register",
            json={
                "username": "guest",
                "password": "secret2",
                "nickname": "게스트",
            },
        )

        guest_login = self.client.post(
            "/api/auth/login",
            json={
                "username": "guest",
                "password": "secret2",
            },
        ).get_json()

        response = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            headers={
                "Authorization":
                    f"Bearer {guest_login['token']}",
            },
            json={
                "dealer_mode": "NIGHT",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )
        self.assertEqual(
            response.get_json()["error"],
            "ONLY_OWNER_CAN_START",
        )

    def test_start_online_room_deals_cards(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            response = self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )
            self.assertEqual(
                response.status_code,
                200,
            )

        response = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "DAY",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.get_data(
                as_text=True
            ),
        )

        selection = response.get_json()

        self.assertEqual(
            selection["mode"],
            "ONLINE",
        )
        self.assertEqual(
            selection["status"],
            "DEALER_SELECTION",
        )
        self.assertIsNotNone(
            selection["dealer_id"],
        )
        self.assertTrue(
            selection[
                "dealer_selection_history"
            ],
        )

        confirm = self.client.post(
            f"/api/online/rooms/{game_id}"
            f"/confirm-start",
            json={
                "owner_id": "OWNER-1",
            },
        )

        self.assertEqual(
            confirm.status_code,
            200,
        )

        data = confirm.get_json()

        self.assertEqual(
            data["mode"],
            "ONLINE",
        )
        self.assertEqual(
            data["status"],
            "PLAYING",
        )
        self.assertEqual(
            data["turn_phase"],
            "DISCARD",
        )
        self.assertIsNotNone(
            data["dealer_id"],
        )
        self.assertEqual(
            data["current_turn_player_id"],
            data["dealer_id"],
        )

        hand_counts = {
            player["player_id"]:
                player["hand_count"]
            for player in data["players"]
        }

        self.assertEqual(
            hand_counts[
                data["dealer_id"]
            ],
            6,
        )

        for player in data["players"]:
            if (
                player["player_id"]
                == data["dealer_id"]
            ):
                continue

            self.assertEqual(
                player["hand_count"],
                5,
            )

        # 3인 시작:
        # 48 - (선 6 + 나머지 5 + 5)
        self.assertEqual(
            data["deck_count"],
            32,
        )

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        all_card_ids = []

        for player in game.state.players:
            all_card_ids.extend(
                card.card_id
                for card in player.hand
            )

        all_card_ids.extend(
            card.card_id
            for card
            in game.state.discard_pile
        )

        all_card_ids.extend(
            card.card_id
            for card
            in game.state.deck.cards
        )

        self.assertEqual(
            len(all_card_ids),
            48,
        )
        self.assertEqual(
            len(set(all_card_ids)),
            48,
        )

    def test_start_online_room_requires_dealer_mode(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )

        response = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.get_json()["error"],
            "DEALER_MODE_REQUIRED",
        )

    def test_started_room_rejects_new_join(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )

        start_response = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "NIGHT",
            },
        )
        self.assertEqual(
            start_response.status_code,
            200,
        )

        response = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "늦은참가자",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.get_json()["error"],
            "ROOM_NOT_WAITING",
        )

    def test_online_websocket_state_hides_other_hands(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )

        self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "DAY",
            },
        )

        self.client.post(
            f"/api/online/rooms/{game_id}"
            f"/confirm-start",
            json={
                "owner_id": "OWNER-1",
            },
        )

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        viewer_id = (
            game.state.players[0].player_id
        )

        data = (
            app_module
            .serialize_game_for_online_player(
                game,
                viewer_id,
            )
        )

        for player in data["players"]:
            if (
                player["player_id"]
                == viewer_id
            ):
                self.assertEqual(
                    len(player["hand"]),
                    player["hand_count"],
                )
            else:
                self.assertEqual(
                    player["hand"],
                    [],
                )
                self.assertGreater(
                    player["hand_count"],
                    0,
                )

    def test_online_join_triggers_realtime_publish(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 4,
            },
        ).get_json()

        game_id = room["game_id"]

        with patch.object(
            app_module.realtime_hub,
            "broadcast_states",
            return_value=0,
        ) as mocked:
            response = self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": "친구1",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
        )
        mocked.assert_called_once()

        called_game_id = (
            mocked.call_args.args[0]
        )
        states = (
            mocked.call_args.args[1]
        )

        self.assertEqual(
            called_game_id,
            game_id,
        )
        self.assertEqual(
            len(states),
            2,
        )

    def test_online_room_get_requires_player_id(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        response = self.client.get(
            f"/api/online/rooms/{game_id}"
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.get_json()["error"],
            "PLAYER_ID_REQUIRED",
        )

    def test_online_action_requires_member_identity(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )

        start = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "DAY",
            },
        ).get_json()

        response = self.client.post(
            f"/api/games/{game_id}/draw"
        )

        self.assertEqual(
            response.status_code,
            403,
        )
        self.assertEqual(
            response.get_json()["error"],
            "PLAYER_ID_REQUIRED",
        )

        response = self.client.post(
            f"/api/games/{game_id}/draw",
            headers={
                "X-Player-ID":
                    "NOT-IN-ROOM",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )
        self.assertEqual(
            response.get_json()["error"],
            "PLAYER_NOT_IN_ROOM",
        )

    def test_online_wrong_player_cannot_draw_for_current_turn(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        joined_ids = []

        for nickname in (
            "친구1",
            "친구2",
        ):
            joined = self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            ).get_json()
            joined_ids.append(
                joined["viewer_player_id"]
            )

        start = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "DAY",
            },
        ).get_json()

        confirm = self.client.post(
            f"/api/online/rooms/{game_id}"
            f"/confirm-start",
            json={
                "owner_id": "OWNER-1",
            },
        ).get_json()

        current_id = (
            confirm["current_turn_player_id"]
        )

        start = confirm

        wrong_id = next(
            player["player_id"]
            for player in start["players"]
            if player["player_id"]
            != current_id
        )

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        current_player = next(
            player
            for player in game.state.players
            if player.player_id
            == current_id
        )

        response = self.client.post(
            f"/api/games/{game_id}/discard",
            headers={
                "X-Player-ID":
                    wrong_id,
            },
            json={
                "card_id":
                    current_player.hand[0].card_id,
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )
        self.assertEqual(
            response.get_json()["error"],
            "NOT_YOUR_TURN",
        )

    def test_dealer_selection_minigame_day_rule(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )

        response = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "DAY",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["status"],
            "DEALER_SELECTION",
        )
        self.assertEqual(
            data["dealer_selection_mode"],
            "DAY",
        )

        history = (
            data["dealer_selection_history"]
        )

        self.assertTrue(
            history
        )

        for draw_round in history:
            months = {
                player_id: card["month"]
                for player_id, card
                in draw_round["draws"].items()
            }

            target = max(
                months.values()
            )

            expected_winners = {
                player_id
                for player_id, month
                in months.items()
                if month == target
            }

            self.assertEqual(
                set(
                    draw_round["winner_ids"]
                ),
                expected_winners,
            )

        self.assertEqual(
            len(
                history[-1]["winner_ids"]
            ),
            1,
        )
        self.assertEqual(
            history[-1]["winner_ids"][0],
            data["dealer_id"],
        )

        # 밤일낮짱 단계에서는 아직 본게임 패를 나누지 않는다.
        self.assertEqual(
            data["deck_count"],
            0,
        )
        self.assertTrue(
            all(
                player["hand_count"] == 0
                for player in data["players"]
            )
        )

    def test_dealer_selection_minigame_night_rule(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )

        data = self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "owner_id": "OWNER-1",
                "dealer_mode": "NIGHT",
            },
        ).get_json()

        self.assertEqual(
            data["dealer_selection_mode"],
            "NIGHT",
        )

        for draw_round in (
            data["dealer_selection_history"]
        ):
            months = {
                player_id: card["month"]
                for player_id, card
                in draw_round["draws"].items()
            }

            target = min(
                months.values()
            )

            expected_winners = {
                player_id
                for player_id, month
                in months.items()
                if month == target
            }

            self.assertEqual(
                set(
                    draw_round["winner_ids"]
                ),
                expected_winners,
            )

    def test_only_owner_can_confirm_after_dealer_selection(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        for nickname in (
            "친구1",
            "친구2",
        ):
            self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": nickname,
                },
            )

        self.client.post(
            f"/api/online/rooms/{game_id}/start",
            json={
                "dealer_mode": "DAY",
            },
        )

        self.client.post(
            "/api/auth/register",
            json={
                "username": "guest2",
                "password": "secret3",
                "nickname": "게스트2",
            },
        )

        guest_login = self.client.post(
            "/api/auth/login",
            json={
                "username": "guest2",
                "password": "secret3",
            },
        ).get_json()

        response = self.client.post(
            f"/api/online/rooms/{game_id}"
            f"/confirm-start",
            headers={
                "Authorization":
                    f"Bearer {guest_login['token']}",
            },
            json={},
        )

        self.assertEqual(
            response.status_code,
            403,
        )
        self.assertEqual(
            response.get_json()["error"],
            "ONLY_OWNER_CAN_START",
        )

    def test_online_discard_without_bbung_moves_to_next_player_draw(self):
        # 랜덤 패 중 "아무도 뻥할 수 없는 버림패"가 나오는
        # 방을 찾은 뒤, 실제 온라인 discard API가
        # 다음 플레이어 DRAW까지 넘기는지 검증한다.
        selected = None

        for attempt in range(50):
            room = self.client.post(
                "/api/online/rooms",
                json={
                    "owner_id":
                        f"OWNER-{attempt}",
                    "nickname": "방장",
                    "max_players": 3,
                },
            ).get_json()

            game_id = room["game_id"]

            for nickname in (
                "친구1",
                "친구2",
            ):
                self.client.post(
                    f"/api/online/rooms/{game_id}/join",
                    json={
                        "nickname":
                            nickname,
                    },
                )

            self.client.post(
                f"/api/online/rooms/{game_id}/start",
                json={
                    "owner_id":
                        f"OWNER-{attempt}",
                    "dealer_mode": "DAY",
                },
            )

            confirm = self.client.post(
                f"/api/online/rooms/{game_id}"
                f"/confirm-start",
                json={
                    "owner_id":
                        f"OWNER-{attempt}",
                },
            ).get_json()

            dealer_id = (
                confirm["dealer_id"]
            )

            game = (
                app_module.manager.get_game(
                    game_id
                )
            )

            dealer = next(
                player
                for player in game.state.players
                if player.player_id
                == dealer_id
            )

            for card in list(
                dealer.hand
            ):
                target_month = (
                    card.month
                )

                bbung_exists = False

                for player in (
                    game.state.players
                ):
                    if (
                        player.player_id
                        == dealer_id
                    ):
                        continue

                    same_month_count = sum(
                        1
                        for hand_card
                        in player.hand
                        if (
                            hand_card.month
                            == target_month
                        )
                    )

                    if (
                        same_month_count >= 2
                        and len(
                            player.hand
                        ) >= 3
                    ):
                        bbung_exists = True
                        break

                if not bbung_exists:
                    selected = (
                        game_id,
                        dealer_id,
                        card.card_id,
                        confirm,
                    )
                    break

            if selected is not None:
                break

        self.assertIsNotNone(
            selected,
            "뻥 후보가 없는 테스트 버림패를 찾지 못했습니다.",
        )

        (
            game_id,
            dealer_id,
            card_id,
            confirm,
        ) = selected

        player_ids = [
            player["player_id"]
            for player
            in confirm["players"]
        ]

        dealer_index = (
            player_ids.index(
                dealer_id
            )
        )

        expected_next_id = (
            player_ids[
                (
                    dealer_index + 1
                )
                % len(player_ids)
            ]
        )

        discard = self.client.post(
            f"/api/games/{game_id}/discard",
            headers={
                "X-Player-ID":
                    dealer_id,
            },
            json={
                "card_id":
                    card_id,
            },
        )

        self.assertEqual(
            discard.status_code,
            200,
            discard.get_data(
                as_text=True
            ),
        )

        data = discard.get_json()

        self.assertEqual(
            data["turn_phase"],
            "DRAW",
        )
        self.assertEqual(
            data[
                "current_turn_player_id"
            ],
            expected_next_id,
        )
        self.assertEqual(
            data[
                "bbung_candidate_player_ids"
            ],
            [],
        )

        draw = self.client.post(
            f"/api/games/{game_id}/draw",
            headers={
                "X-Player-ID":
                    expected_next_id,
            },
        )

        self.assertEqual(
            draw.status_code,
            200,
            draw.get_data(
                as_text=True
            ),
        )

        draw_data = (
            draw.get_json()
        )

        self.assertEqual(
            draw_data["turn_phase"],
            "DISCARD",
        )
        self.assertEqual(
            draw_data[
                "current_turn_player_id"
            ],
            expected_next_id,
        )

    def test_duplicate_join_same_client_id_is_idempotent(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "client_id": "CLIENT-OWNER",
                "nickname": "방장",
                "max_players": 4,
            },
        ).get_json()

        game_id = room["game_id"]

        first = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구1",
                "client_id": "CLIENT-A",
            },
        )

        self.assertEqual(
            first.status_code,
            200,
        )

        first_data = first.get_json()
        first_player_id = (
            first_data["viewer_player_id"]
        )

        second = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구1",
                "client_id": "CLIENT-A",
            },
        )

        self.assertEqual(
            second.status_code,
            200,
        )

        second_data = second.get_json()

        self.assertEqual(
            second_data["viewer_player_id"],
            first_player_id,
        )
        self.assertTrue(
            second_data["already_joined"]
        )
        self.assertEqual(
            len(second_data["players"]),
            2,
        )

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        self.assertEqual(
            len(game.state.players),
            2,
        )

    def test_room_owner_clicking_join_again_does_not_create_p2(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "client_id": "CLIENT-OWNER",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        response = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "방장",
                "client_id": "CLIENT-OWNER",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["viewer_player_id"],
            f"{game_id}-P1",
        )
        self.assertTrue(
            data["already_joined"]
        )
        self.assertEqual(
            len(data["players"]),
            1,
        )

    def test_duplicate_join_still_returns_existing_when_room_is_full(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-1",
                "client_id": "CLIENT-OWNER",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        first = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구1",
                "client_id": "CLIENT-A",
            },
        ).get_json()

        self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구2",
                "client_id": "CLIENT-B",
            },
        )

        duplicate = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "친구1",
                "client_id": "CLIENT-A",
            },
        )

        self.assertEqual(
            duplicate.status_code,
            200,
        )

        data = duplicate.get_json()

        self.assertTrue(
            data["already_joined"]
        )
        self.assertEqual(
            data["viewer_player_id"],
            first["viewer_player_id"],
        )
        self.assertEqual(
            len(data["players"]),
            3,
        )

    def _make_online_tie_break_room(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-TIE",
                "client_id": "CLIENT-OWNER",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        joined = []

        for index in range(2):
            data = self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname":
                        f"친구{index + 1}",
                    "client_id":
                        f"CLIENT-{index + 2}",
                },
            ).get_json()
            joined.append(
                data["viewer_player_id"]
            )

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        p1 = (
            game.state.players[0].player_id
        )
        p2 = (
            game.state.players[1].player_id
        )
        p3 = (
            game.state.players[2].player_id
        )

        state = game.state
        state.status = GameStatus.TIE_BREAK
        state.tie_break_player_ids = [
            p1,
            p2,
        ]
        state.tie_break_drawn_cards = {
            p1: [],
            p2: [],
        }
        state.tie_break_current_player_index = 0
        state.tie_break_round_number = 1
        state.tie_break_deck = (
            app_module.Deck()
        )

        # draw()은 pop()이므로 뒤에서부터 사용된다.
        # P1: 12, 11, 10 = 33
        # P2: 1, 2, 3 = 6
        # 실제 순서는 P1,P2,P1,P2,P1,P2.
        state.tie_break_deck.cards = [
            Card(6, 1),
            Card(3, 1),
            Card(10, 1),
            Card(2, 1),
            Card(11, 1),
            Card(1, 1),
            Card(12, 1),
        ]

        return (
            game_id,
            p1,
            p2,
            p3,
        )

    def test_online_final_tie_break_wrong_player_cannot_draw(self):
        (
            game_id,
            p1,
            p2,
            _p3,
        ) = self._make_online_tie_break_room()

        response = self.client.post(
            f"/api/games/{game_id}"
            f"/tie-break/draw",
            headers={
                "X-Player-ID": p2,
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )
        self.assertEqual(
            response.get_json()["error"],
            "NOT_YOUR_TIE_BREAK_TURN",
        )

        # 올바른 현재 참가자는 정상 드로우.
        response = self.client.post(
            f"/api/games/{game_id}"
            f"/tie-break/draw",
            headers={
                "X-Player-ID": p1,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        data = response.get_json()

        self.assertEqual(
            data[
                "tie_break_current_player_id"
            ],
            p2,
        )
        self.assertEqual(
            len(
                data["tie_break_drawn_cards"][
                    p1
                ]
            ),
            1,
        )

    def test_online_non_tie_break_player_cannot_draw(self):
        (
            game_id,
            _p1,
            _p2,
            p3,
        ) = self._make_online_tie_break_room()

        response = self.client.post(
            f"/api/games/{game_id}"
            f"/tie-break/draw",
            headers={
                "X-Player-ID": p3,
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )
        self.assertEqual(
            response.get_json()["error"],
            "NOT_TIE_BREAK_PLAYER",
        )

    def test_online_final_tie_break_can_finish_game(self):
        (
            game_id,
            p1,
            p2,
            _p3,
        ) = self._make_online_tie_break_room()

        order = [
            p1,
            p2,
            p1,
            p2,
            p1,
            p2,
        ]

        last_data = None

        for player_id in order:
            response = self.client.post(
                f"/api/games/{game_id}"
                f"/tie-break/draw",
                headers={
                    "X-Player-ID":
                        player_id,
                },
            )

            self.assertEqual(
                response.status_code,
                200,
                response.get_data(
                    as_text=True
                ),
            )

            last_data = (
                response.get_json()
            )

        self.assertEqual(
            last_data["status"],
            "GAME_END",
        )
        self.assertEqual(
            last_data["game_winner_id"],
            p1,
        )

        self.assertEqual(
            [
                card["month"]
                for card
                in last_data[
                    "tie_break_drawn_cards"
                ][p1]
            ],
            [12, 11, 10],
        )
        self.assertEqual(
            [
                card["month"]
                for card
                in last_data[
                    "tie_break_drawn_cards"
                ][p2]
            ],
            [1, 2, 3],
        )

    def _make_online_bbung_reaction_room(
        self,
    ):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-BBUNG",
                "client_id": "CLIENT-P1",
                "nickname": "P1",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]
        p1 = room["viewer_player_id"]

        p2 = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "P2",
                "client_id": "CLIENT-P2",
            },
        ).get_json()[
            "viewer_player_id"
        ]

        p3 = self.client.post(
            f"/api/online/rooms/{game_id}/join",
            json={
                "nickname": "P3",
                "client_id": "CLIENT-P3",
            },
        ).get_json()[
            "viewer_player_id"
        ]

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        state = game.state
        state.status = GameStatus.PLAYING
        state.turn_phase = (
            app_module.TurnPhase.DISCARD
        )
        state.current_turn_player_id = p1
        state.dealer_id = p1
        state.deck = app_module.Deck()

        players = {
            player.player_id: player
            for player in state.players
        }

        players[p1].hand = [
            Card(5, 3),
            Card(8, 1),
            Card(9, 1),
        ]

        players[p2].hand = [
            Card(1, 1),
            Card(2, 1),
            Card(3, 1),
        ]

        players[p3].hand = [
            Card(5, 1),
            Card(5, 2),
            Card(7, 1),
        ]

        state.discard_pile = []
        state.last_discarded_card = None
        state.last_discarded_by_player_id = None
        state.bbung_candidate_player_ids = []
        state.bbung_reaction_deadline = None

        return (
            game_id,
            p1,
            p2,
            p3,
        )

    def test_online_bbung_timeout_auto_advances_to_next_draw(self):
        (
            game_id,
            p1,
            p2,
            p3,
        ) = (
            self
            ._make_online_bbung_reaction_room()
        )

        with patch.object(
            app_module.GameEngine,
            "BBUNG_REACTION_SECONDS",
            0.05,
        ):
            response = self.client.post(
                f"/api/games/{game_id}/discard",
                headers={
                    "X-Player-ID": p1,
                },
                json={
                    "card_id": "05-03",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
            response.get_data(
                as_text=True
            ),
        )

        immediate = response.get_json()

        self.assertEqual(
            immediate["turn_phase"],
            "REACTION",
        )
        self.assertEqual(
            immediate[
                "bbung_candidate_player_ids"
            ],
            [p3],
        )

        time.sleep(
            0.15
        )

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        self.assertEqual(
            game.state.turn_phase,
            app_module.TurnPhase.DRAW,
        )
        self.assertEqual(
            game.state.current_turn_player_id,
            p2,
        )
        self.assertEqual(
            game.state.bbung_candidate_player_ids,
            [],
        )
        self.assertIsNone(
            game.state.bbung_reaction_deadline
        )

    def test_online_bbung_pass_cancels_server_timeout(self):
        (
            game_id,
            p1,
            p2,
            p3,
        ) = (
            self
            ._make_online_bbung_reaction_room()
        )

        with patch.object(
            app_module.GameEngine,
            "BBUNG_REACTION_SECONDS",
            0.20,
        ):
            discard = self.client.post(
                f"/api/games/{game_id}/discard",
                headers={
                    "X-Player-ID": p1,
                },
                json={
                    "card_id": "05-03",
                },
            )

        self.assertEqual(
            discard.status_code,
            200,
        )

        passed = self.client.post(
            f"/api/games/{game_id}/bbung/pass",
            headers={
                "X-Player-ID": p3,
            },
        )

        self.assertEqual(
            passed.status_code,
            200,
            passed.get_data(
                as_text=True
            ),
        )

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        self.assertEqual(
            game.state.turn_phase,
            app_module.TurnPhase.DRAW,
        )
        self.assertEqual(
            game.state.current_turn_player_id,
            p2,
        )

        time.sleep(
            0.30
        )

        self.assertEqual(
            game.state.turn_phase,
            app_module.TurnPhase.DRAW,
        )
        self.assertEqual(
            game.state.current_turn_player_id,
            p2,
        )

    def test_online_bbung_timeout_publishes_realtime_state(self):
        (
            game_id,
            p1,
            _p2,
            _p3,
        ) = (
            self
            ._make_online_bbung_reaction_room()
        )

        with (
            patch.object(
                app_module.GameEngine,
                "BBUNG_REACTION_SECONDS",
                0.05,
            ),
            patch.object(
                app_module,
                "publish_online_state",
                wraps=(
                    app_module
                    .publish_online_state
                ),
            ) as mocked_publish,
        ):
            response = self.client.post(
                f"/api/games/{game_id}/discard",
                headers={
                    "X-Player-ID": p1,
                },
                json={
                    "card_id": "05-03",
                },
            )

            self.assertEqual(
                response.status_code,
                200,
            )

            time.sleep(
                0.15
            )

            # 1회 이상은 after_request,
            # 추가 1회는 서버 타이머의 자동 턴 전환 방송.
            self.assertGreaterEqual(
                mocked_publish.call_count,
                2,
            )

    def test_online_successful_post_emits_operational_log(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-LOG",
                "client_id": "CLIENT-LOG-OWNER",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        with patch.object(
            app_module,
            "log_game_event",
        ) as mocked_log:
            response = self.client.post(
                f"/api/online/rooms/{game_id}/join",
                json={
                    "nickname": "친구1",
                    "client_id": "CLIENT-LOG-P2",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            any(
                call.kwargs.get("action")
                == (
                    f"/api/online/rooms/"
                    f"{game_id}/join"
                )
                and call.kwargs.get("result")
                == "OK"
                for call
                in mocked_log.call_args_list
            )
        )

    def test_online_failed_post_emits_operational_log(self):
        room = self.client.post(
            "/api/online/rooms",
            json={
                "owner_id": "OWNER-LOG-FAIL",
                "client_id": "CLIENT-LOG-FAIL",
                "nickname": "방장",
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        with patch.object(
            app_module,
            "log_game_event",
        ) as mocked_log:
            response = self.client.post(
                f"/api/online/rooms/{game_id}/start",
                json={
                    "owner_id": "WRONG-OWNER",
                    "dealer_mode": "DAY",
                },
            )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertTrue(
            any(
                call.kwargs.get("result")
                == "HTTP_400"
                for call
                in mocked_log.call_args_list
            )
        )

    def test_bbung_timeout_emits_named_operational_log(self):
        (
            game_id,
            p1,
            _p2,
            _p3,
        ) = (
            self
            ._make_online_bbung_reaction_room()
        )

        with (
            patch.object(
                app_module.GameEngine,
                "BBUNG_REACTION_SECONDS",
                0.05,
            ),
            patch.object(
                app_module,
                "log_game_event",
            ) as mocked_log,
        ):
            response = self.client.post(
                f"/api/games/{game_id}/discard",
                headers={
                    "X-Player-ID": p1,
                },
                json={
                    "card_id": "05-03",
                },
            )

            self.assertEqual(
                response.status_code,
                200,
            )

            time.sleep(
                0.15
            )

            self.assertTrue(
                any(
                    call.kwargs.get("action")
                    == "BBUNG_TIMEOUT_AUTO_PASS"
                    and call.kwargs.get("result")
                    == "OK"
                    for call
                    in mocked_log.call_args_list
                )
            )

if __name__ == "__main__":
    unittest.main()
