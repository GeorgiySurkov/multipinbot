from tortoise.models import Model
from tortoise import fields


class PinnedMessage(Model):
    class Meta:
        table = 'pinned_messages'
    id = fields.IntField(pk=True)
    text = fields.CharField(max_length=4096)
    telegram_id = fields.IntField()
    sent = fields.DatetimeField()


class Group(Model):
    class Meta:
        table = 'group'
    id = fields.IntField(pk=True)
    telegram_id = fields.IntField()
    global_pinned_message_id = fields.IntField()
