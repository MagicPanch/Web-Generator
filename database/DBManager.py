import datetime
from pymongo.mongo_client import MongoClient
from mongoengine import connect
import CONSTANTS
from database.colections.Page import Page
from database.colections.User import User


class DBManager(object):

    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = DBManager()
        return cls._instance

    def __init__(self) -> None:
        if DBManager._instance is None:
            DBManager._instance = self
            self._client = MongoClient(CONSTANTS.DB_URI)
            connect(
                db='web_generator',  # Nombre de la base de datos
                host=CONSTANTS.DB_URI)
        else:
            raise Exception("No se puede crear otra instancia de DB Manager")

    def add_user(self, id, username, nombre):
        user = User.objects(id=id)
        print(user)
        if not user:
            user = User(id=id, username=username, name=nombre, paginas=[])
            user.save()
            print("----USUARIO INSERTADO EN LA DB----")
        else:
            print("----USUARIO YA EXISTENTE EN LA DB----")

    def add_page(self, user_id, page_name, contact, webType):
        user = User.objects(id=user_id).first()
        if user:
            page_id = user_id + '-' + page_name
            page = Page(id=page_id, name=page_name, contact=contact, creationDate=datetime.datetime.now(), lastModification=datetime.datetime.now(), compiled=False)
            page.save()
            user.paginas.append(page)
            user.save()
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")

    def get_page(self, user_id, page_name):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            return page
        else:
            return None

    def get_page_by_name(self, page_name):
        page = Page.objects(id__icontains=page_name).first()
        if page:
            return page
        else:
            return None

    def get_user_pages(self, user_id):
        user = User.objects(id=user_id).first()
        if user:
            return user.paginas
        else:
            return None

    def was_compiled(self, user_id, page_name):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            return page.compiled
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    def set_page_mail(self, user_id, page_name, page_mail):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.mail = page_mail
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    def set_page_location(self, user_id, page_name, page_location):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.location = page_location
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")
