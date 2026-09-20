import unittest

import app as app_module


REQUIRED_GAME_KEYS = {
    "ok",
    "game_id",
    "status",
    "turn_phase",
    "dealer_id",
    "current_turn_player_id",
    "round_number",
    "deck_count",
    "discard_pile",
    "players",
    "bbung_candidate_player_ids",
    "active_bagaji_declarations",
    "active_bomb_bagaji_declarations",
}


class ApiGameFlowTests(
    unittest.TestCase
):
    def setUp(self):
        app_module.app.config.update(
            TESTING=True
        )

        app_module.manager.games.clear()

        self.client = (
            app_module.app.test_client()
        )

    def assert_full_game_payload(
        self,
        data,
    ):
        self.assertIsInstance(
            data,
            dict,
        )

        missing = (
            REQUIRED_GAME_KEYS
            - set(data.keys())
        )

        self.assertFalse(
            missing,
            (
                "전체 게임 응답에서 "
                f"키가 누락됐습니다: "
                f"{sorted(missing)}"
            ),
        )

        self.assertIsInstance(
            data["players"],
            list,
            "players는 반드시 배열이어야 합니다.",
        )

        self.assertEqual(
            len(data["players"]),
            3,
        )

        for player in data["players"]:
            self.assertIn(
                "player_id",
                player,
            )
            self.assertIn(
                "hand",
                player,
            )
            self.assertIsInstance(
                player["hand"],
                list,
            )

    def get_state(
        self,
        game_id,
    ):
        response = self.client.get(
            f"/api/games/{game_id}"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.get_data(
                as_text=True
            ),
        )

        data = response.get_json()

        self.assert_full_game_payload(
            data
        )

        return data

    def create_game(
        self,
        difficulty,
    ):
        response = self.client.post(
            "/api/games",
            json={
                "owner_id": "TEST-USER",
                "nickname": "테스터",
                "ai_difficulty": difficulty,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.get_data(
                as_text=True
            ),
        )

        data = response.get_json()

        self.assert_full_game_payload(
            data
        )

        ai_players = [
            player
            for player in data["players"]
            if (
                player["player_type"]
                == "BOT"
            )
        ]

        self.assertTrue(
            all(
                player["ai_difficulty"]
                == difficulty
                for player in ai_players
            )
        )

        self.assertEqual(
            data["status"],
            "DEALER_SELECTION",
        )
        self.assertIn(
            data["dealer_selection_mode"],
            {"DAY", "NIGHT"},
        )

        return data["game_id"]

    def post_and_require_success(
        self,
        url,
        json_data=None,
    ):
        response = self.client.post(
            url,
            json=json_data,
        )

        self.assertEqual(
            response.status_code,
            200,
            (
                f"{url}\n"
                + response.get_data(
                    as_text=True
                )
            ),
        )

        return response.get_json()

    def play_until_round(
        self,
        difficulty,
        target_round=4,
    ):
        game_id = self.create_game(
            difficulty
        )

        action_count = 0

        while True:
            action_count += 1

            self.assertLess(
                action_count,
                3000,
                (
                    "API 게임 진행이 "
                    "무한 루프에 빠졌습니다."
                ),
            )

            state = self.get_state(
                game_id
            )

            if (
                state["round_number"]
                >= target_round
            ):
                return

            if (
                state["status"]
                == "DEALER_SELECTION"
            ):
                result = (
                    self.post_and_require_success(
                        f"/api/games/"
                        f"{game_id}/dealer-selection/draw"
                    )
                )
                self.assert_full_game_payload(
                    result
                )
                continue

            if (
                state["status"]
                == "ROUND_END"
            ):
                result = (
                    self.post_and_require_success(
                        f"/api/games/"
                        f"{game_id}/next-round"
                    )
                )

                self.assert_full_game_payload(
                    result
                )

                continue

            self.assertEqual(
                state["status"],
                "PLAYING",
                (
                    "테스트 중 예상하지 못한 "
                    f"상태입니다: "
                    f"{state['status']}"
                ),
            )

            human = next(
                player
                for player
                in state["players"]
                if (
                    player["player_type"]
                    == "HUMAN"
                )
            )

            human_id = (
                human["player_id"]
            )

            if (
                state["turn_phase"]
                == "REACTION"
            ):
                candidates = (
                    state[
                        "bbung_candidate_player_ids"
                    ]
                )

                if human_id in candidates:
                    self.post_and_require_success(
                        f"/api/games/"
                        f"{game_id}/bbung/pass"
                    )
                else:
                    result = (
                        self.post_and_require_success(
                            f"/api/games/"
                            f"{game_id}/continue"
                        )
                    )

                    # /continue 응답은 브라우저가
                    # 직접 renderGame()에 넣으므로
                    # 반드시 전체 상태여야 한다.
                    self.assert_full_game_payload(
                        result
                    )

                continue

            if (
                state[
                    "current_turn_player_id"
                ]
                != human_id
            ):
                result = (
                    self.post_and_require_success(
                        f"/api/games/"
                        f"{game_id}/continue"
                    )
                )

                self.assert_full_game_payload(
                    result
                )

                continue

            if (
                state["turn_phase"]
                == "DRAW"
            ):
                self.post_and_require_success(
                    f"/api/games/"
                    f"{game_id}/draw"
                )

                state = self.get_state(
                    game_id
                )

                # 드로우 순간 덱이 소진되면
                # 라운드 종료 또는 Phase 전환이 발생할 수 있다.
                # 이 경우 DISCARD를 강제하지 않고
                # 다음 루프에서 상태에 맞게 처리한다.
                if (
                    state["status"]
                    != "PLAYING"
                    or state["turn_phase"]
                    != "DISCARD"
                ):
                    continue

            self.assertEqual(
                state["turn_phase"],
                "DISCARD",
            )

            human = next(
                player
                for player
                in state["players"]
                if (
                    player["player_type"]
                    == "HUMAN"
                )
            )

            self.assertTrue(
                human["hand"]
            )

            card_id = (
                human["hand"][0][
                    "card_id"
                ]
            )

            self.post_and_require_success(
                f"/api/games/"
                f"{game_id}/discard",
                {
                    "card_id": card_id,
                },
            )

            # 실제 브라우저 흐름처럼
            # 버린 뒤 AI 진행 API를 호출한다.
            current = self.get_state(
                game_id
            )

            if (
                current["status"]
                == "PLAYING"
            ):
                if (
                    current["turn_phase"]
                    == "REACTION"
                    and human_id
                    in current[
                        "bbung_candidate_player_ids"
                    ]
                ):
                    continue

                result = (
                    self.post_and_require_success(
                        f"/api/games/"
                        f"{game_id}/continue"
                    )
                )

                self.assert_full_game_payload(
                    result
                )

    def test_beginner_browser_like_flow(self):
        self.play_until_round(
            "BEGINNER",
            target_round=4,
        )

    def test_intermediate_browser_like_flow(self):
        self.play_until_round(
            "INTERMEDIATE",
            target_round=4,
        )

    def test_advanced_browser_like_flow(self):
        self.play_until_round(
            "ADVANCED",
            target_round=4,
        )

    def test_tazza_browser_like_flow(self):
        self.play_until_round(
            "TAZZA",
            target_round=4,
        )


if __name__ == "__main__":
    unittest.main()
