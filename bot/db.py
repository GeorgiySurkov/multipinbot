from tortoise import Tortoise


async def init(config):
    await Tortoise.init(
        db_url=config.DATABASE_URI,
        modules={'models': ['bot.models']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()


async def shutdown():
    await Tortoise.close_connections()
