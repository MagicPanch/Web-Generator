import datetime
from typing import List, Dict, Tuple

from pymongo.mongo_client import MongoClient
from mongoengine import connect, Document, ObjectIdField

from database.collections.particular.Product import Product
from resources import CONSTANTS
from database.collections.general.EcommerceSection import EcommerceSection
from database.collections.general.User import User
from database.collections.general.Page import Page
from database.collections.general.InformativeSection import InformativeSection


class DBManager(object):

    _instance = None
    _client = None
    _db = None
    _product_id: Dict[Tuple[str, str], int] = {}

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = DBManager()
        return cls._instance

    def __init__(self) -> None:
        if DBManager._instance is None:
            DBManager._instance = self
            self._product_id = {}
            self._client = MongoClient(CONSTANTS.DB_URI)
            self._db = self._client['web_generator']
            connect(
                db='web_generator',  # Nombre de la base de datos
                host=CONSTANTS.DB_URI,
                uuidRepresentation='standard')
        else:
            raise Exception("No se puede crear otra instancia de DB Manager")


    def _get_product_id(self, user, page) -> int:
        print("--------en _GET_PRODUCT_ID--------")
        if (user, page) in self._product_id.keys():
            print("------------usuario y pagina existen en la coleccion--------")
            self._product_id[(user, page)] += 1
            print("------------p_id incrementado:", self._product_id[(user, page)])
            return self._product_id[(user, page)] - 1
        else:
            print("------------usuario y pagina no existen en la coleccion--------")
            self._product_id[(user, page)] = 1
            print("------------p_id a retornar:", self._product_id[(user, page)])
            return self._product_id[(user, page)]


    def add_user(self, user_id, username, nombre):
        user = User.objects(id=user_id).first()
        if not user:
            user = User(id=user_id, username=username, name=nombre, paginas=[], hizo_tutorial=False)
            user.save()


    def get_user(self, user_id) -> User:
        user = User.objects(id=user_id).first()
        if user:
            return user
        else:
            return None


    def set_user_tutorial(self, user_id):
        user = User.objects(id=user_id).first()
        if user:
            user.hizo_tutorial = True
            user.save()
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")


    def get_user_tutorial(self, user_id) -> bool:
        user = User.objects(id=user_id).first()
        if user:
            return user.hizo_tutorial
        else:
            return False


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


    def get_page(self, user_id, page_name) -> Page:
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            return page
        else:
            return None


    def get_page_by_name(self, page_name) -> Page:
        pages = Page.objects(id__icontains=page_name)
        found = False
        for page in pages:
            if page.name == page_name:
                return page
        if not found:
            return None


    def get_user_pages(self, user_id) -> List[Page]:
        user = User.objects(id=user_id).first()
        if user:
            if len(user.paginas) > 0:
                return user.paginas
            else:
                return None
        else:
            return None


    def was_compiled(self, user_id, page_name) -> bool:
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


    def add_inf_section(self, user_id, page_name, inf_section):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            section_id = page_id + '-' + inf_section.get_title()
            section = InformativeSection(id=section_id, type="informativa", title=inf_section.get_title(), text=inf_section.get_text())
            section.save()
            page.sections.append(section)
            page.lastModificationDate = datetime.datetime.now()
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    def add_ecomm_section(self, user_id, page_name):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            section_id = page_id + '-' + "ecommerce"
            section = EcommerceSection(id=section_id, type="ecommerce")
            section.save()
            page.sections.append(section)
            page.has_ecomm_section = True
            page.lastModificationDate = datetime.datetime.now()
            page.product_counter = 0
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")


    def updt_inf_section(self, user_id, page_name, section_title, inf_section):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            old_section_id = page_id + '-' + section_title
            old_section = InformativeSection.objects(id=old_section_id).first()
            new_section = InformativeSection(id=page_id + '-' + inf_section.get_title(), type="informativa", title=inf_section.get_title(), text=inf_section.get_text())
            new_section.save()
            page.sections = [new_section if section.id == old_section_id else section for section in page.sections]
            page.lastModificationDate = datetime.datetime.now()
            page.save()
            old_section.delete()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")


    def get_page_sections(self, user_id, page_name) -> List[Document]:
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            expanded_sections = []
            for section in page.sections:
                expanded_sections.append(section)
            return expanded_sections
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")


    def add_product(self, user_id, page_name, cant, title, desc, precio) -> int:
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            p_id = page.product_counter
            collection = self._db[page_id]
            if collection:
                product = {
                    "key": p_id,
                    "stock": cant,
                    "name": title,
                    "desc": desc,
                    "price": precio,
                }
                collection.insert_one(product)
                page.product_counter += 1
                page.save()
            return p_id
        else:
            raise Exception("La pagina " + str(page) + " no existe o no te pertenece")

    def set_product_multimedia(self, user_id, page_name, product, media_url):
        page_id = user_id + '-' + page_name
        collection = self._db[page_id]
        if collection:
            collection.update_one({"key": product}, {"$set": {"multimedia": media_url}})

