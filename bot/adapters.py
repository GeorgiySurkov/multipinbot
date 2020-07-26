from aiosqlite import Cursor, Connection, connect, Row
from typing import Optional, Tuple, Iterable
from datetime import datetime
import contextlib


class DbAdapter:
    def __init__(self, db_path: str):
        self.conn: Optional[Connection] = None
        self.db_path = db_path

    async def get_connection(self):
        if self.conn is None:
            self.conn = await connect(self.db_path)
            # self.connect.row_factory = aiosqlite.Row
        return self.conn

    @contextlib.asynccontextmanager
    async def execute(self, statement: str, values: Optional[Tuple] = None, commit: bool = False) -> Cursor:
        conn = await self.get_connection()
        cursor = await conn.execute(statement, values)
        try:
            yield cursor
        finally:
            if commit:
                await conn.commit()

    @contextlib.asynccontextmanager
    async def executescript(self, script: str, commit: bool = False) -> Cursor:
        conn = await self.get_connection()
        cursor = await conn.executescript(script)
        try:
            yield cursor
        finally:
            if commit:
                await conn.commit()

    async def create_tables(self) -> None:
        script = """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_message_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            sent TEXT NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY(chat_id) REFERENCES chats(telegram_chat_id)
        );

        CREATE TABLE IF NOT EXISTS chats (
            telegram_chat_id INTEGER NOT NULL,
            pinned_message_id INTEGER NOT NULL,
            PRIMARY KEY(telegram_chat_id)
        )
        """
        async with self.executescript(script, commit=True):
            return None

    async def get_chat_by_id(self, chat_id) -> Optional[Row]:
        sql = """
        SELECT *
        FROM chats
        WHERE telegram_chat_id=?
        """
        values = (chat_id,)
        async with self.execute(sql, values) as cursor:
            return await cursor.fetchone()

    async def add_pinned_message(self, message_id: int, chat_id: int, author_id: int, sent: datetime,
                                 text: str) -> None:
        sql = """
        INSERT
        INTO messages (telegram_message_id, chat_id, author_id, sent, text)
        VALUES (?, ?, ?, ?, ?)
        """
        iso_sent = sent.replace(microsecond=0).isoformat()
        values = (message_id, chat_id, author_id, iso_sent, text)
        async with self.execute(sql, values, commit=True):
            return

    async def get_chat_pinned_messages(self, chat_id: int) -> Iterable[Row]:
        sql = """
        SELECT *
        FROM messages
        WHERE chat_id = ?
        """
        values = (chat_id, )
        async with self.execute(sql, values) as cursor:
            return await cursor.fetchall()

    async def delete_pinned_message(self, telegram_message_id: int) -> None:
        sql = """
        DELETE
        FROM messages
        WHERE telegram_message_id = ?
        """
        values = (telegram_message_id, )
        async with self.execute(sql, values, commit=True):
            return

    async def close(self) -> None:
        if self.conn is not None:
            await self.conn.close()
            self.conn = None
