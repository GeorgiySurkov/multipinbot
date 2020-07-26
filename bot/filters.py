from aiogram.dispatcher.filters import BoundFilter
from aiogram import types


class BotAddedToGroup(BoundFilter):
    key = 'bot_id'

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    def check(self, message: types.Message) -> bool:
        return self.bot_id in [user.id for user in message.new_chat_members]
