from game.instance import GameInstance, GameMode


class GameManager:
    """
    서버에서 여러 게임방을 관리한다.
    """

    def __init__(self) -> None:
        self.games: dict[str, GameInstance] = {}

    def add_game(self, game: GameInstance) -> None:
        """
        새로운 게임방을 등록한다.
        """
        if game.game_id in self.games:
            raise ValueError(
                f"이미 존재하는 game_id입니다: {game.game_id}"
            )

        self.games[game.game_id] = game

    def get_game(self, game_id: str) -> GameInstance | None:
        """
        game_id로 게임방을 찾는다.
        """
        return self.games.get(game_id)

    def remove_game(self, game_id: str) -> None:
        """
        종료된 게임방을 제거한다.
        """
        self.games.pop(game_id, None)

    def get_games_by_mode(
        self,
        mode: GameMode,
    ) -> list[GameInstance]:
        """
        특정 모드의 게임방만 반환한다.
        """
        return [
            game
            for game in self.games.values()
            if game.mode == mode
        ]

    def require_mode(
        self,
        game_id: str,
        mode: GameMode,
    ) -> GameInstance:
        """
        지정한 game_id가 존재하고
        요청한 모드와 일치하는지 검증한다.
        """
        game = self.get_game(game_id)

        if game is None:
            raise ValueError(
                "GAME_NOT_FOUND"
            )

        if game.mode != mode:
            raise ValueError(
                "GAME_MODE_MISMATCH"
            )

        return game

