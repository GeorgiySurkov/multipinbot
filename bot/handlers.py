from aiogram import types
from tortoise.exceptions import DoesNotExist

from . import dp, bot
from .filters import BotAddedToGroup
from .models import Group, PinnedMessage
from .services import is_msg_supported, update_or_create_global_pinned_message


@dp.message_handler(commands=['help', 'start'])
async def start(msg: types.Message) -> None:
    """
    This handler will be called when user sends `/start` or `/help` command.
    """
    if msg.chat.type == 'private':
        await msg.reply("Hi!\nI'm MultiPin Bot!\nAdd me to any group to pin multiple messages at the same time.")
    else:
        await msg.reply("To pin messages reply to it with /pin command.")


@dp.message_handler(lambda msg: msg.text is not None and msg.text.startswith('/unpin'))
async def unpin_command(msg: types.Message) -> None:
    """
    This handler will be called when user unpins message with '/unpin<msg_id>'
    """
    command = msg.text
    try:
        pinned_msg_id = int(command[6:])
    except ValueError:
        return
    try:
        pinned_msg = await PinnedMessage.get(telegram_id=pinned_msg_id)
    except DoesNotExist:
        await msg.answer('Message does not exist.')
        return
    if pinned_msg.group.telegram_id != msg.chat.id:
        await msg.answer('Message does not exist.')
        return
    await pinned_msg.delete()
    current_group = await Group.get(telegram_id=msg.chat.id)
    await update_or_create_global_pinned_message(bot, current_group)


@dp.message_handler(commands=['pin'])
async def pin_command(msg: types.Message) -> None:
    """
    This handler will be called when user pins message with '/pin' command
    """
    if msg.reply_to_message is None:
        await msg.answer("To pin message reply to it with /pin command")
        return
    if not await is_msg_supported(msg):
        await msg.answer("Sorry, this type of message is not supported. For now I support only text messages.")
    current_group = await Group.get(telegram_id=msg.chat.id)
    new_pinned_msg = PinnedMessage(
        group=current_group,
        text=msg.reply_to_message.text,
        telegram_id=msg.reply_to_message.message_id,
        sent=msg.reply_to_message.date,
        author_id=msg.from_user.id
    )
    await new_pinned_msg.save()
    await update_or_create_global_pinned_message(bot, current_group, new_pinned_msg)


@dp.message_handler(content_types=[types.ContentType.PINNED_MESSAGE])
async def pin(msg: types.Message) -> None:
    """
    This handler will be called when user pins a message without command.
    """
    await msg.answer('This group is using @multipinbot. To pin a message reply to it with /pin command.')
    current_group = await Group.get(telegram_id=msg.chat.id)
    if current_group.global_pinned_message_id is not None:
        await msg.chat.pin_message(current_group.global_pinned_message_id)
        return
    await update_or_create_global_pinned_message(bot, current_group)


@dp.message_handler(BotAddedToGroup(bot.id), content_types=[types.ContentType.NEW_CHAT_MEMBERS])
async def added_to_group(msg: types.Message) -> None:
    """
    This handler will be called when bot was added to group.
    """
    await msg.answer("Hi, I'm @multipinbot. I can pin multiple messages in group."
                     " To pin a message reply to it with /pin command.")
    current_group, is_created = await Group.get_or_create({'telegram_id': msg.chat.id}, telegram_id=msg.chat.id)
    if is_created:
        await current_group.save()
