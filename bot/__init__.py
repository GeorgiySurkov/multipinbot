from aiogram import Bot, Dispatcher, executor, types
from logging.config import dictConfig
import asyncio

from . import db
from .config import Config
from .logging_config import LOGGING


# Configure logging
dictConfig(LOGGING)

bot = Bot(token=Config.TELEGRAM_TOKEN)
dp = Dispatcher(bot)


def run():
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(db.init(Config))
        executor.start_polling(dp, skip_updates=True)
    finally:
        # Graceful shutdown
        loop.run_until_complete(db.shutdown())


from . import handlers
