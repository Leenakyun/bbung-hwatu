import json
import queue
import threading
from collections import defaultdict


class OnlineRealtimeHub:
    """
    Flask와 같은 HTTP 포트에서 동작하는
    SSE(Server-Sent Events)용 온라인 상태 허브.

    게임 행동은 기존 REST API가 담당하고,
    실시간 상태 갱신만 서버 -> 브라우저 방향으로 전송한다.
    """

    def __init__(
        self,
        room_player_validator=None,
    ) -> None:
        self.room_player_validator = (
            room_player_validator
        )

        self.clients = defaultdict(dict)
        self.lock = threading.Lock()

    def register_client(
        self,
        game_id: str,
        player_id: str,
    ):
        client_queue = queue.Queue(
            maxsize=20
        )

        with self.lock:
            self.clients[
                game_id
            ][
                client_queue
            ] = player_id

        return client_queue

    def unregister_client(
        self,
        game_id: str,
        client_queue,
    ) -> None:
        with self.lock:
            room_clients = (
                self.clients.get(
                    game_id
                )
            )

            if room_clients is None:
                return

            room_clients.pop(
                client_queue,
                None,
            )

            if not room_clients:
                self.clients.pop(
                    game_id,
                    None,
                )

    def broadcast_states(
        self,
        game_id: str,
        states_by_player_id: dict[
            str,
            dict,
        ],
    ) -> int:
        """
        같은 방 접속자에게 각자 전용 상태를 큐로 전달한다.
        """
        with self.lock:
            room_clients = dict(
                self.clients.get(
                    game_id,
                    {},
                )
            )

        if not room_clients:
            return 0

        delivered = 0

        for (
            client_queue,
            player_id,
        ) in room_clients.items():
            game_state = (
                states_by_player_id.get(
                    player_id
                )
            )

            if game_state is None:
                continue

            payload = {
                "type": "STATE_UPDATE",
                "game_id": game_id,
                "game": game_state,
            }

            try:
                client_queue.put_nowait(
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                    )
                )
                delivered += 1

            except queue.Full:
                # 느린 클라이언트는 가장 오래된 상태 하나를 버리고
                # 최신 상태를 다시 넣는다.
                try:
                    client_queue.get_nowait()
                except queue.Empty:
                    pass

                try:
                    client_queue.put_nowait(
                        json.dumps(
                            payload,
                            ensure_ascii=False,
                        )
                    )
                    delivered += 1
                except queue.Full:
                    pass

        return delivered
