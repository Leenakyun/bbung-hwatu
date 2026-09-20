import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash


class AuthError(ValueError):
    pass


class AuthStore:
    def __init__(self, db_path: str, session_days: int = 30) -> None:
        self.db_path = str(Path(db_path))
        self.session_days = session_days
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            connection.commit()

    @staticmethod
    def _normalize_username(username: str) -> str:
        return username.strip().lower()

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def register(self, username: str, password: str, nickname: str) -> dict:
        username = self._normalize_username(username)
        nickname = nickname.strip()

        if len(username) < 3:
            raise AuthError("아이디는 3자 이상이어야 합니다.")
        if len(username) > 30:
            raise AuthError("아이디는 30자 이하여야 합니다.")
        if len(password) < 6:
            raise AuthError("비밀번호는 6자 이상이어야 합니다.")
        if not nickname:
            raise AuthError("닉네임을 입력해 주세요.")
        if len(nickname) > 20:
            raise AuthError("닉네임은 20자 이하여야 합니다.")

        now = datetime.now(timezone.utc).isoformat()
        password_hash = generate_password_hash(password)

        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO users (
                        username, password_hash, nickname, created_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (username, password_hash, nickname, now),
                )
                connection.commit()
                user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise AuthError("이미 사용 중인 아이디입니다.")

        return {
            "user_id": user_id,
            "username": username,
            "nickname": nickname,
        }

    def login(self, username: str, password: str) -> dict:
        username = self._normalize_username(username)

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT user_id, username, password_hash, nickname
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

            if row is None or not check_password_hash(
                row["password_hash"], password
            ):
                raise AuthError("아이디 또는 비밀번호가 올바르지 않습니다.")

            token = secrets.token_urlsafe(32)
            token_hash = self._token_hash(token)
            now_dt = datetime.now(timezone.utc)
            now = now_dt.isoformat()
            expires_at = (
                now_dt + timedelta(days=self.session_days)
            ).isoformat()

            connection.execute(
                """
                INSERT INTO auth_sessions (
                    user_id, token_hash, created_at, expires_at
                ) VALUES (?, ?, ?, ?)
                """,
                (row["user_id"], token_hash, now, expires_at),
            )
            connection.execute(
                """
                UPDATE users
                SET last_login_at = ?
                WHERE user_id = ?
                """,
                (now, row["user_id"]),
            )
            connection.commit()

        return {
            "token": token,
            "user": {
                "user_id": row["user_id"],
                "username": row["username"],
                "nickname": row["nickname"],
            },
        }

    def get_user_by_token(self, token: str | None) -> dict | None:
        if not token:
            return None

        token_hash = self._token_hash(token)
        now = datetime.now(timezone.utc)

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.nickname,
                    s.expires_at
                FROM auth_sessions s
                JOIN users u ON u.user_id = s.user_id
                WHERE s.token_hash = ?
                """,
                (token_hash,),
            ).fetchone()

            if row is None:
                return None

            expires_at = datetime.fromisoformat(row["expires_at"])
            if expires_at <= now:
                connection.execute(
                    "DELETE FROM auth_sessions WHERE token_hash = ?",
                    (token_hash,),
                )
                connection.commit()
                return None

            return {
                "user_id": row["user_id"],
                "username": row["username"],
                "nickname": row["nickname"],
            }

    def logout(self, token: str | None) -> None:
        if not token:
            return

        token_hash = self._token_hash(token)

        with self._connect() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE token_hash = ?",
                (token_hash,),
            )
            connection.commit()

    def clear_for_tests(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM auth_sessions")
            connection.execute("DELETE FROM users")
            connection.commit()
