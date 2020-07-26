import os


class Config:
    DATABASE_URI = os.getenv('DATABASE_URI', 'db.sqlite')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
