import threading
from pymongo.mongo_client import MongoClient
import CONSTANTS

class DBManager(object):

    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = DBManager()
        return cls._instance

    def __init__(self) -> None:
        if DBManager._instance is None:
            DBManager._instance = self
            self._client = MongoClient(CONSTANTS.DB_URI)
            self._lock = threading.Lock()
        else:
            raise Exception("No se puede crear otra instancia de DB Manager")

    def add_user_page(self, user, page):
        pass


