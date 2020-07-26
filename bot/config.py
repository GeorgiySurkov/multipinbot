import os


class Config:
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'db.sqlite')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
