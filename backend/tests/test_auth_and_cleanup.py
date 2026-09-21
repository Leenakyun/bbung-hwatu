import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import app as app_module


class AuthAndCleanupTests(unittest.TestCase):
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

    def _register_and_login(
        self,
        username="tester",
        nickname="테스터",
    ):
        register = self.client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": "secret1",
                "nickname": nickname,
            },
        )

        self.assertEqual(
            register.status_code,
            200,
            register.get_data(
                as_text=True
            ),
        )

        login = self.client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": "secret1",
            },
        )

        self.assertEqual(
            login.status_code,
            200,
            login.get_data(
                as_text=True
            ),
        )

        return login.get_json()

    def test_register_login_me_logout(self):
        login = self._register_and_login()

        token = login["token"]

        me = self.client.get(
            "/api/auth/me",
            headers={
                "Authorization":
                    f"Bearer {token}",
            },
        )

        self.assertEqual(
            me.status_code,
            200,
        )
        self.assertEqual(
            me.get_json()["user"][
                "username"
            ],
            "tester",
        )

        logout = self.client.post(
            "/api/auth/logout",
            headers={
                "Authorization":
                    f"Bearer {token}",
            },
        )

        self.assertEqual(
            logout.status_code,
            200,
        )

        me_after = self.client.get(
            "/api/auth/me",
            headers={
                "Authorization":
                    f"Bearer {token}",
            },
        )

        self.assertEqual(
            me_after.status_code,
            401,
        )


    def test_existing_user_can_login_from_new_client_session(self):
        register = self.client.post(
            "/api/auth/register",
            json={
                "username": "returning",
                "password": "secret1",
                "nickname": "재접속",
            },
        )
        self.assertEqual(register.status_code, 200)

        fresh_client = app_module.app.test_client()
        login = fresh_client.post(
            "/api/auth/login",
            json={
                "username": "returning",
                "password": "secret1",
            },
        )

        self.assertEqual(login.status_code, 200)
        payload = login.get_json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["token"])
        self.assertEqual(payload["user"]["username"], "returning")

    def test_new_login_invalidates_previous_device_session(self):
        first = self._register_and_login(
            username="single-session",
            nickname="단일접속",
        )
        first_token = first["token"]

        second_client = app_module.app.test_client()
        second_login = second_client.post(
            "/api/auth/login",
            json={
                "username": "single-session",
                "password": "secret1",
            },
        )
        self.assertEqual(second_login.status_code, 200)
        second_token = second_login.get_json()["token"]
        self.assertNotEqual(first_token, second_token)

        first_me = self.client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {first_token}",
            },
        )
        self.assertEqual(first_me.status_code, 401)

        second_me = second_client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {second_token}",
            },
        )
        self.assertEqual(second_me.status_code, 200)


    def test_password_is_not_stored_as_plain_text(self):
        self._register_and_login()

        with sqlite3.connect(
            app_module.AUTH_DB_PATH
        ) as connection:
            row = connection.execute(
                """
                SELECT password_hash
                FROM users
                WHERE username = ?
                """,
                ("tester",),
            ).fetchone()

        self.assertIsNotNone(
            row
        )
        self.assertNotEqual(
            row[0],
            "secret1",
        )
        self.assertNotIn(
            "secret1",
            row[0],
        )

    def test_online_room_requires_login(self):
        response = self.client.post(
            "/api/online/rooms",
            json={
                "nickname": "방장",
                "max_players": 3,
            },
        )

        self.assertEqual(
            response.status_code,
            401,
        )
        self.assertEqual(
            response.get_json()["error"],
            "AUTH_REQUIRED",
        )

    def test_authenticated_user_can_create_room(self):
        login = self._register_and_login()

        response = self.client.post(
            "/api/online/rooms",
            headers={
                "Authorization":
                    f"Bearer {login['token']}",
            },
            json={
                "max_players": 3,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["owner_id"],
            f"USER-{login['user']['user_id']}",
        )
        self.assertEqual(
            data["players"][0][
                "nickname"
            ],
            "테스터",
        )

    def test_stale_online_room_is_deleted(self):
        login = self._register_and_login()

        room = self.client.post(
            "/api/online/rooms",
            headers={
                "Authorization":
                    f"Bearer {login['token']}",
            },
            json={
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        game.last_activity_at = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                hours=7
            )
        )

        with patch.object(
            app_module,
            "ROOM_TTL_HOURS",
            6,
        ):
            removed = (
                app_module
                .cleanup_stale_online_rooms()
            )

        self.assertIn(
            game_id,
            removed,
        )
        self.assertIsNone(
            app_module.manager.get_game(
                game_id
            )
        )

    def test_recent_online_room_is_not_deleted(self):
        login = self._register_and_login()

        room = self.client.post(
            "/api/online/rooms",
            headers={
                "Authorization":
                    f"Bearer {login['token']}",
            },
            json={
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]

        game = (
            app_module.manager.get_game(
                game_id
            )
        )

        game.last_activity_at = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                hours=5,
                minutes=59,
            )
        )

        with patch.object(
            app_module,
            "ROOM_TTL_HOURS",
            6,
        ):
            removed = (
                app_module
                .cleanup_stale_online_rooms()
            )

        self.assertNotIn(
            game_id,
            removed,
        )
        self.assertIsNotNone(
            app_module.manager.get_game(
                game_id
            )
        )


    def test_sse_requires_valid_login_token(self):
        response = self.client.get(
            "/events/ROOM-NOT-REAL"
            "?player_id=P1"
            "&token=BAD-TOKEN",
        )

        self.assertEqual(
            response.status_code,
            401,
        )
        self.assertEqual(
            response.get_json()["error"],
            "AUTH_REQUIRED",
        )

    def test_sse_connects_for_authenticated_room_player(self):
        login = self._register_and_login()

        room = self.client.post(
            "/api/online/rooms",
            headers={
                "Authorization":
                    f"Bearer {login['token']}",
            },
            json={
                "max_players": 3,
            },
        ).get_json()

        game_id = room["game_id"]
        player_id = (
            room["viewer_player_id"]
        )

        response = self.client.get(
            f"/events/{game_id}"
            f"?player_id={player_id}"
            f"&token={login['token']}",
            buffered=False,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.mimetype,
            "text/event-stream",
        )

        first_chunk = next(
            response.response
        ).decode(
            "utf-8"
        )

        self.assertIn(
            '"type": "CONNECTED"',
            first_chunk,
        )
        self.assertIn(
            game_id,
            first_chunk,
        )

        response.close()

if __name__ == "__main__":
    unittest.main()
