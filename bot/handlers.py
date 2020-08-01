from aiogram import types
from aiogram.utils.exceptions import BadRequest
from tortoise.exceptions import DoesNotExist
from logging import getLogger
from aiogram.utils.exceptions import NotEnoughRightsToPinMessage

from . import dp, bot
from .filters import BotAddedToGroup
from .models import Group, PinnedMessage
from .services import is_msg_supported, update_or_create_global_pinned_message, unpin_pattern, message_thumbnail


logger = getLogger(__name__)


@dp.message_handler(commands=['help', 'start'])
async def start(msg: types.Message) -> None:
    """
    This handler will be called when user sends `/start` or `/help` command.
    """
    if msg.chat.type == 'private':
        await msg.answer("Hi!\nI'm MultiPin Bot!\nAdd me to any group to pin multiple messages at the same time.")
    else:
        await msg.answer("To pin messages reply to it with /pin command.")


@dp.message_handler(regexp=unpin_pattern)
async def unpin_command(msg: types.Message) -> None:
    """
    This handler will be called when user unpins message with '/unpin<msg_id>'
    """
    res = unpin_pattern.match(msg.text)
    pinned_msg_id = int(res.group(1))
    try:
        pinned_msg = await PinnedMessage.get(id=pinned_msg_id)
    except DoesNotExist:
        await msg.answer('Message does not exist.')
        return
    await pinned_msg.fetch_related('group')
    if pinned_msg.group.telegram_id != msg.chat.id:
        await msg.answer('Message does not exist.')
        return
    await pinned_msg.delete()
    current_group = await Group.get(telegram_id=msg.chat.id)
    await update_or_create_global_pinned_message(bot, current_group)
    try:
        await bot.send_message(msg.chat.id, "Successfully removed from pinned messages!", reply_to_message_id=pinned_msg.telegram_id)
    except BadRequest as e:
        if str(e) == 'Reply message not found':
            await bot.send_message(msg.chat.id, f"Successfully removed from pinned messages {message_thumbnail(pinned_msg.text)} !")
        else:
            raise
    logger.info(f'Unpinned message tg_id:{pinned_msg.telegram_id} in group "{msg.chat.title}" tg_id:{msg.chat.id}')


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
    current_group, is_created = await Group.get_or_create({'title': msg.chat.title}, telegram_id=msg.chat.id)
    if is_created:
        logger.warning(
            f'Group "{msg.chat.title}" tg_id:{msg.chat.id} has not been added to database when bot was added to group.'
        )
    already_pinned_message = await PinnedMessage.get_or_none(
        telegram_id=msg.reply_to_message.message_id,
        group=current_group
    )
    if already_pinned_message is not None:
        await msg.answer("This message is already pinned!")
        return
    new_pinned_msg = PinnedMessage(
        group=current_group,
        text=msg.reply_to_message.text,
        telegram_id=msg.reply_to_message.message_id,
        sent=msg.reply_to_message.date,
        author_id=msg.from_user.id
    )
    await new_pinned_msg.save()
    await update_or_create_global_pinned_message(bot, current_group, new_pinned_msg)
    await msg.reply_to_message.reply("Successfully added to pinned messages!")
    logger.info(f'Pinned message tg_id:{new_pinned_msg.telegram_id} in group "{msg.chat.title}" tg_id:{msg.chat.id}')


@dp.message_handler(lambda msg: msg.from_user.id != bot.id, content_types=[types.ContentType.PINNED_MESSAGE])
async def pin(msg: types.Message) -> None:
    """
    This handler will be called when user pins a message without command.
    """
    await msg.answer('This group is using @multipinbot. To pin a message reply to it with /pin command.')
    current_group, is_created = await Group.get_or_create({'title': msg.chat.title}, telegram_id=msg.chat.id)
    if is_created:
        await current_group.save()
        logger.warning(
            f'Group "{msg.chat.title}" tg_id:{msg.chat.id} has not been added to database when bot was added to group.'
        )
    if current_group.global_pinned_message_id is not None:
        try:
            await msg.chat.pin_message(current_group.global_pinned_message_id)
            current_group.is_pinned_global_message = True
        except NotEnoughRightsToPinMessage:
            await msg.answer('I need rights to pin messages.')
            current_group.is_pinned_global_message = False
    await current_group.save()
    # await update_or_create_global_pinned_message(bot, current_group)


@dp.message_handler(BotAddedToGroup(bot.id), content_types=[types.ContentType.NEW_CHAT_MEMBERS])
@dp.message_handler(content_types=[types.ContentType.GROUP_CHAT_CREATED])
async def added_to_group(msg: types.Message) -> None:
    """
    This handler will be called when bot was added to group.
    """
    await msg.answer("Hi, I'm @multipinbot. I can pin multiple messages in group.\n\n"
                     "To use my functionality you need to grant me rights to pin messages in group."
                     " To pin a message reply to it with /pin command.")
    a = 2 / 0
    current_group, is_created = await Group.get_or_create({'title': msg.chat.title}, telegram_id=msg.chat.id)
    if is_created:
        await current_group.save()
    logger.info(f'Bot added to group "{msg.chat.title}", tg_id:{msg.chat.id}')


@dp.message_handler(content_types=[types.ContentType.NEW_CHAT_TITLE])
async def new_title(msg: types.Message):
    current_group, is_created = await Group.get_or_create({'title': msg.chat.title}, telegram_id=msg.chat.id)
    if is_created:
        logger.warning(
            f'Group "{msg.chat.title}" tg_id:{msg.chat.id} has not been added to database when bot was added to group.'
        )
        await current_group.save()
    else:
        old_title = current_group.title
        current_group.title = msg.chat.title
        await current_group.save()
        logger.info(f'Changed group tg_id:{current_group.telegram_id} title'
                    f' from "{old_title}" to "{current_group.title}"')
