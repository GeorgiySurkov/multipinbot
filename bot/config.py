import os


class Config:
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite://db.sqlite3')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    DEPLOY = os.getenv('DEPLOY', 0) == 1

    WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'https://deploy-heroku-bot.herokuapp.com')  # name your app
    WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook/')
    WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

    WEBAPP_HOST = '0.0.0.0'
    WEBAPP_PORT = os.getenv('PORT')
