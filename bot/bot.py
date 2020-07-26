from aiogram import types
import aiogram
from typing import Iterable
from aiosqlite import Row
from datetime import datetime

from .adapters import DbAdapter
from .exceptions import TooLongMessageText


class TelegramBot:
    def __init__(self, token: str, db_adapter: DbAdapter):
        self.bot = aiogram.Bot(token=token)
        self.dp = aiogram.Dispatcher(self.bot)
        self.db_adapter = db_adapter

        # Register handlers
        # self.dp.register_message_handler(self.echo)
        self.dp.register_message_handler(self.send_welcome, commands=['start', 'help'])
        self.dp.register_message_handler(self.pin_command, commands=['pin'])
        # self.dp.register_message_handler(self.)

    async def make_pin_message(self, pinned_messages: Iterable[Row]) -> str:
        """
        Function to form a message to pin that will contain other pinned messages.
        :param pinned_messages: list of messages from database
        :return:
        """
        formatted_messages = []
        for msg in pinned_messages:
            msg_id, tg_msg_id, chat_id, author_id, sent, text = msg
            author = await self.bot.get_chat_member(chat_id, author_id)  # TODO handle case if user left the chat
            humanized_time = datetime.fromisoformat(sent).strftime('%d %B, %H:%M')
            formatted_messages.append(f'{author.user.mention} at {humanized_time}:\n{text}')
        if len(formatted_messages) == 0:
            return "Here will be your pinned messages!"
        msg = '\n\n'.join(formatted_messages)
        if len(msg) > 4096:
            raise TooLongMessageText('Too much pinned messages.\nUnpin some messages to free space.')
        return msg

    @staticmethod
    async def echo(message: types.Message) -> None:
        print(message.text)
        await message.answer(f'{message.text}\n{message.url}')

    @staticmethod
    async def send_welcome(message: types.Message) -> None:
        """
        This handler will be called when user sends `/start` or `/help` command
        """
        await message.reply("Hi!\nI'm MultiPin Bot!\nAdd me to any group to pin multiple messages at the same time.")

    async def pin_command(self, message: types.Message) -> None:
        """
        This handler will be called when user wants to pin a message using /pin command
        """
        if message.reply_to_message is None:
            await message.answer("To pin a message reply to it with /pin command")
            return
        await self.db_adapter.add_pinned_message(
            message.reply_to_message.message_id,
            message.chat.id,
            message.from_user.id,
            message.date,
            message.reply_to_message.text
        )
        pinned_messages = await self.db_adapter.get_chat_pinned_messages(message.chat.id)
        try:
            new_pinned_message_text = await self.make_pin_message(pinned_messages)
        except TooLongMessageText as e:
            await self.db_adapter.delete_pinned_message(message.reply_to_message.message_id)
            await message.answer(str(e))
            return
        current_chat = await self.db_adapter.get_chat_by_id(message.chat.id)
        global_pinned_message_id = current_chat[1]
        await message.bot.edit_message_text(
            new_pinned_message_text,
            message.chat.id,
            global_pinned_message_id
        )
        await message.answer('Successfully pinned message!')

    async def pin(self, message: types.Message):
        await message.reply('This chat is using MultiPin bot. To pin a message reply to it with command /pin')
        current_chat = await self.db_adapter.get_chat_by_id(message.chat.id)
        if current_chat is not None:
            pinned_message_id = current_chat[1]
            await message.chat.pin_message(pinned_message_id)

    def start_polling(self) -> None:
        aiogram.executor.start_polling(self.dp)

    async def close(self) -> None:
        pass
