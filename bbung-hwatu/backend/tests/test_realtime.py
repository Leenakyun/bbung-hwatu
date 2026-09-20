import json
import queue
import unittest

from game.realtime import (
    OnlineRealtimeHub,
)


class RealtimeHubTests(
    unittest.TestCase
):
    def setUp(self):
        self.hub = OnlineRealtimeHub()

    def test_room_broadcast_is_isolated_and_personalized(self):
        queue_p1 = (
            self.hub.register_client(
                "ROOM-001",
                "ROOM-001-P1",
            )
        )

        queue_p2 = (
            self.hub.register_client(
                "ROOM-001",
                "ROOM-001-P2",
            )
        )

        queue_other = (
            self.hub.register_client(
                "ROOM-002",
                "ROOM-002-P1",
            )
        )

        delivered = (
            self.hub.broadcast_states(
                "ROOM-001",
                {
                    "ROOM-001-P1": {
                        "viewer": "P1",
                        "secret": "HAND-P1",
                    },
                    "ROOM-001-P2": {
                        "viewer": "P2",
                        "secret": "HAND-P2",
                    },
                },
            )
        )

        self.assertEqual(
            delivered,
            2,
        )

        update1 = json.loads(
            queue_p1.get_nowait()
        )
        update2 = json.loads(
            queue_p2.get_nowait()
        )

        self.assertEqual(
            update1["game"]["secret"],
            "HAND-P1",
        )
        self.assertEqual(
            update2["game"]["secret"],
            "HAND-P2",
        )

        with self.assertRaises(
            queue.Empty
        ):
            queue_other.get_nowait()

    def test_unregister_client_removes_connection(self):
        client_queue = (
            self.hub.register_client(
                "ROOM-001",
                "ROOM-001-P1",
            )
        )

        self.hub.unregister_client(
            "ROOM-001",
            client_queue,
        )

        delivered = (
            self.hub.broadcast_states(
                "ROOM-001",
                {
                    "ROOM-001-P1": {
                        "viewer": "P1",
                    },
                },
            )
        )

        self.assertEqual(
            delivered,
            0,
        )


if __name__ == "__main__":
    unittest.main()
