import logging
import asyncio

from .config import Config
from .adapters import DbAdapter
from .bot import TelegramBot


class Application:
    def __init__(self):
        self.config = Config

        self.db_adapter = DbAdapter(Config.DATABASE_PATH)

        self.bot = TelegramBot(Config.TELEGRAM_TOKEN, self.db_adapter)
        logging.basicConfig(level=logging.INFO)

    async def init(self) -> None:
        """
        Async initialization.
        """
        await self.db_adapter.create_tables()

    def run(self):
        self.bot.start_polling()

    async def shutdown(self) -> None:
        await self.db_adapter.close()
        await self.bot.close()


def run():
    loop = asyncio.get_event_loop()
    app = Application()

    try:
        # Asynchronous initialization
        loop.run_until_complete(app.init())
        app.run()
    finally:
        # Graceful shutdown
        loop.run_until_complete(app.shutdown())
