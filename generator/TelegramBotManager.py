from anyio import Path
from telegram import Bot, File

from resources import CONSTANTS


class TelegramBotManager:

    _bot = None
    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = TelegramBotManager()
        return cls._instance

    def __init__(self) -> None:
        if TelegramBotManager._instance is None:
            TelegramBotManager._instance = self
            TelegramBotManager._bot = Bot(token=CONSTANTS.TELEGRAM_BOT_TOKEN)
        else:
            raise Exception("No se puede crear otra instancia de TelegranBotManager")

    @staticmethod
    def download_image(page_path, subdir, image_id, image_name):
        file = TelegramBotManager._bot.get_file(image_id)
        download_path = Path(page_path)
        download_path.joinpath(subdir).joinpath(image_name)
        file.download(custom_path=download_path)

    @staticmethod
    def get_csv_file(file_id) -> File:
        file = TelegramBotManager._bot.get_file(file_id)
        return file