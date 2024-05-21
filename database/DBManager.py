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
                host=CONSTANTS.DB_URI,
                uuidRepresentation='standard')
        else:
            raise Exception("No se puede crear otra instancia de DB Manager")

    def add_user(self, id, username, nombre):
        user = User.objects(id=id).first()
        if not user:
            user = User(id=id, username=username, name=nombre, paginas=[], hizo_tutorial=False)
            user.save()

    def get_user(self, id):
        user = User.objects(id=id).first()
        if user:
            return user
        else:
            return None

    def add_page(self, user_id, page_name, contact):
        user = User.objects(id=user_id).first()
        if user:
            page_id = user_id + '-' + page_name
            page = Page(id=page_id, name=page_name, contact=contact, creationDate=datetime.datetime.utcnow(), lastModificationDate=datetime.datetime.now())
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
        pages = Page.objects(id__icontains=page_name)
        found = False
        for page in pages:
            if page.name == page_name:
                return page
        if not found:
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
            if page.compilationDate is None:
                return False
            else:
                return page.compilationDate >= page.lastModificationDate
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    def set_page_mail(self, user_id, page_name, page_mail):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.mail = page_mail
            page.lastModificationDate = datetime.datetime.now()
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    def set_page_location(self, user_id, page_name, page_location):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.location = page_location
            page.lastModificationDate = datetime.datetime.now()
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    def updt_modification_date(self, user_id, page_name):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.lastModificationDate = datetime.datetime.now()
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    def set_compilation_date(self, user_id, page_name):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.compilationDate = datetime.datetime.now()
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")
