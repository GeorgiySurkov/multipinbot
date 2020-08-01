from logging import getLogger

from . import dp


logger = getLogger(__name__)


@dp.errors_handler()
async def global_error_handler(update, exception) -> bool:
    logger.exception('Exception occurred')
    return True
