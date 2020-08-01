from tortoise.models import Model
from tortoise import fields


class PinnedMessage(Model):
    class Meta:
        table = 'pinned_message'
        unique_together = (('telegram_id', 'group_id'),)
    id = fields.IntField(pk=True)
    group = fields.ForeignKeyField('models.Group', related_name='pinned_messages')
    text = fields.CharField(max_length=4096)
    author_id = fields.IntField()
    telegram_id = fields.IntField()
    sent = fields.DatetimeField()


class Group(Model):
    class Meta:
        table = 'group'
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=128)
    telegram_id = fields.IntField(unique=True)
    global_pinned_message_id = fields.IntField(null=True)
    global_pinned_message_text = fields.CharField(max_length=4096, null=True)
    is_pinned_global_message = fields.BooleanField(default=False)
