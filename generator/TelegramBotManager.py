import os

import requests
from anyio import Path
from telegram import Bot, File, InputFile

from resources import CONSTANTS


class TelegramBotManager:

    _bot = None
    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = TelegramBotManager()
        return cls._instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelegramBotManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Comprobar si ya está inicializado
            self._instance = self
            self._bot = Bot(token=CONSTANTS.TELEGRAM_BOT_TOKEN)
            self._initialized = True  # Marcar como inicializado

    @classmethod
    def download_image(cls, page_path, subdir, image_id, image_name):
        file = cls._bot.get_file(image_id)
        download_path = Path(os.getcwd())
        download_path = download_path.joinpath(page_path).joinpath(subdir).joinpath(image_name)
        file.download(custom_path=download_path)

    @classmethod
    def get_csv_file(cls, file_id) -> File:
        file = cls._bot.get_file(file_id)
        return file

    @classmethod
    def send_file_to_user(cls, user_id, file_path):
        with open(file_path, "rb") as file:
            cls._bot.send_document(chat_id=user_id, document=file)

    @staticmethod
    def get_image_url(image_id) -> str:
        url = f'https://api.telegram.org/bot{CONSTANTS.TELEGRAM_BOT_TOKEN}/getFile?file_id={image_id}'
        response = requests.get(url)
        data = response.json()
        file_path = data['result']['file_path']
        # Construye la URL completa de la imagen
        image_url = f'https://api.telegram.org/file/bot{CONSTANTS.TELEGRAM_BOT_TOKEN}/{file_path}'
        print(image_url)
        return image_url
