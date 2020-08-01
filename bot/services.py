from typing import List, Optional, Tuple
from aiogram import Bot, types
from aiogram.utils.exceptions import NotEnoughRightsToPinMessage
import re

from .models import PinnedMessage, Group
from .exceptions import TooLongMessageText


async def make_global_pinned_message(bot: Bot, pinned_messages: List[PinnedMessage]) -> str:
    formatted_messages = []
    if len(pinned_messages) > 0:
        await PinnedMessage.fetch_for_list(pinned_messages, 'group')
    for msg in pinned_messages:
        author = await bot.get_chat_member(msg.group.telegram_id, msg.author_id)
        formatted_messages.append(
            f'{author.user.mention} at {msg.sent.strftime("%d %B, %H:%M")}:\n'
            f'{msg.text}\n'
            f'/unpin{msg.id} to unpin this message'
        )
    if len(formatted_messages) == 0:
        return "No pinned messages!"
    msg = '\n\n'.join(formatted_messages)
    if len(msg) > 4096:
        raise TooLongMessageText('Too much pinned messages.\nUnpin some messages to free space.')
    return msg


async def make_global_pinned_message_for_group(bot: Bot, group: Group) -> str:
    pinned_messages = await PinnedMessage.filter(group=group).order_by('-sent').all()
    return await make_global_pinned_message(bot, pinned_messages)


async def get_new_global_pinned_message_text(bot: Bot,
                                             current_group: Group,
                                             new_pinned_msg: Optional[PinnedMessage] = None
                                             ) -> Tuple[bool, str]:
    """
    Gets global pinned message text from database or makes new if needed.
    :param bot:
    :param current_group:
    :param new_pinned_msg: pass it if user tried to pin new message.
    :return: tuple of two values: is_updated and global_pinned_message_text
    """
    if new_pinned_msg is not None:
        try:
            global_pinned_message_text = await make_global_pinned_message_for_group(bot, current_group)
        except TooLongMessageText as e:
            await new_pinned_msg.delete()
            await bot.send_message(
                current_group.telegram_id,
                str(e)
            )
            if current_group.global_pinned_message_text is not None:
                global_pinned_message_text = current_group.global_pinned_message_text
            else:
                global_pinned_message_text = await make_global_pinned_message_for_group(bot, current_group)
    else:
        if current_group.global_pinned_message_text is not None:
            global_pinned_message_text = current_group.global_pinned_message_text
        else:
            global_pinned_message_text = await make_global_pinned_message_for_group(bot, current_group)
    is_updated = global_pinned_message_text != current_group.global_pinned_message_text
    return is_updated, global_pinned_message_text


async def update_or_create_global_pinned_message(bot: Bot,
                                                 current_group: Group,
                                                 new_pinned_msg: Optional[PinnedMessage] = None
                                                 ) -> None:
    """
    Updates or creates global pinned message and returns if it was successful.
    """
    if current_group.global_pinned_message_id is None:
        # If global pinned message has not been sent yet (e.g. bot was added to group recently)
        await create_global_pinned_message(bot, current_group, new_pinned_msg)
    else:
        await update_global_pinned_message(bot, current_group, new_pinned_msg)


async def create_global_pinned_message(bot: Bot,
                                       current_group: Group,
                                       new_pinned_msg: Optional[PinnedMessage] = None
                                       ) -> None:
    """
    Sends global message to pin to group, pins it and updates global pinned message id in database
    """
    _, global_pinned_message_text = await get_new_global_pinned_message_text(
        bot,
        current_group,
        new_pinned_msg
    )
    global_pinned_message = await bot.send_message(current_group.telegram_id, global_pinned_message_text)
    current_group.global_pinned_message_id = global_pinned_message.message_id
    try:
        await bot.pin_chat_message(current_group.telegram_id, global_pinned_message.message_id)
    except NotEnoughRightsToPinMessage:
        await bot.send_message(current_group.telegram_id, 'I need rights to pin messages.')
        await current_group.save()
        return
    current_group.is_pinned_global_message = True
    await current_group.save()


async def update_global_pinned_message(bot: Bot,
                                       current_group: Group,
                                       new_pinned_msg: Optional[PinnedMessage] = None
                                       ) -> None:
    is_updated, global_pinned_message_text = await get_new_global_pinned_message_text(
        bot,
        current_group,
        new_pinned_msg
    )
    if is_updated:
        await bot.edit_message_text(
            global_pinned_message_text,
            current_group.telegram_id,
            current_group.global_pinned_message_id
        )
    if not current_group.is_pinned_global_message:
        try:
            await bot.pin_chat_message(current_group.telegram_id, current_group.global_pinned_message_id)
        except NotEnoughRightsToPinMessage:
            await bot.send_message(current_group.telegram_id, 'I need rights to pin messages.')
            return
        current_group.is_pinned_global_message = True
    await current_group.save()


async def is_msg_supported(msg: types.Message) -> bool:
    return msg.text is not None


def message_thumbnail(msg_text: str) -> str:
    if len(msg_text) > 10:
        return msg_text[:8] + '...'
    return msg_text


unpin_pattern = re.compile(r'^/unpin(\d+)(@multipinbot)?$')
