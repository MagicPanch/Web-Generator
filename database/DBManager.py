import datetime
from typing import List, Dict, Tuple

from pymongo.mongo_client import MongoClient
from mongoengine import connect, Document

from resources import CONSTANTS
from database.collections.general.User import User
from database.collections.general.Page import Page
from database.collections.general.InformativeSection import InformativeSection
from database.collections.general.EcommerceSection import EcommerceSection


class DBManager:

    _instance = None
    _client = None
    _db = None
    _product_id: Dict[Tuple[str, str], int] = {}

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = DBManager()
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Comprobar si ya está inicializado
            self._client = MongoClient(CONSTANTS.DB_URI)
            self._db = self._client['web_generator']
            connect(
                db='web_generator',  # Nombre de la base de datos
                host=CONSTANTS.DB_URI,
                uuidRepresentation='standard')
            self._initialized = True  # Marcar como inicializado

    @staticmethod
    def add_user(user_id, username, nombre):
        user = User.objects(id=user_id).first()
        if not user:
            user = User(id=user_id, username=username, name=nombre, paginas=[], hizo_tutorial=False)
            user.save()

    @staticmethod
    def get_user(user_id) -> User:
        user = User.objects(id=user_id).first()
        if user:
            return user
        else:
            return None

    @staticmethod
    def set_user_tutorial(user_id):
        user = User.objects(id=user_id).first()
        if user:
            user.hizo_tutorial = True
            user.save()
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")

    @staticmethod
    def get_user_tutorial(user_id) -> bool:
        user = User.objects(id=user_id).first()
        if user:
            return user.hizo_tutorial
        else:
            return False

    @staticmethod
    def add_page(user_id, page_name, contact):
        user = User.objects(id=user_id).first()
        if user:
            page_id = user_id + '-' + page_name
            page = Page(id=page_id, name=page_name, contact=contact, creationDate=datetime.datetime.utcnow(), lastModificationDate=datetime.datetime.now())
            page.save()
            user.paginas.append(page)
            user.save()
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")

    @staticmethod
    def get_page(user_id, page_name) -> Page:
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            return page
        else:
            return None

    @staticmethod
    def get_page_by_name(page_name) -> Page:
        pages = Page.objects(id__icontains=page_name)
        found = False
        for page in pages:
            if page.name == page_name:
                return page
        if not found:
            return None

    @staticmethod
    def get_user_pages(user_id, section=None) -> List[Page]:
        user = User.objects(id=user_id).first()
        if user:
            if len(user.paginas) > 0:
                if section is not None:
                    output = []
                    for page in user.paginas:
                        sections = page.sections
                        for section in sections:
                            if section.name == section:
                                output.append(page)
                    return output
                else:
                    return user.paginas
            else:
                return []
        else:
            return []

    @staticmethod
    def was_compiled(user_id, page_name) -> bool:
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            if page.compilationDate is None:
                return False
            else:
                return page.compilationDate >= page.lastModificationDate
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    @staticmethod
    def set_page_mail(user_id, page_name, page_mail):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.mail = page_mail
            page.lastModificationDate = datetime.datetime.now()
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    @staticmethod
    def set_page_location(user_id, page_name, page_location):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.location = page_location
            page.lastModificationDate = datetime.datetime.now()
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    @staticmethod
    def updt_modification_date(user_id, page_name):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.lastModificationDate = datetime.datetime.now()
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    @staticmethod
    def set_compilation_date(user_id, page_name, port):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            page.compilationDate = datetime.datetime.now()
            page.port = port
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    @staticmethod
    def add_inf_section(user_id, page_name, inf_section):
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

    @staticmethod
    def add_ecomm_section(user_id, page_name):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            section_id = page_id + '-' + "ecommerce"
            section = EcommerceSection(id=section_id, type="e-commerce")
            section.save()
            page.sections.append(section)
            page.has_ecomm_section = True
            page.lastModificationDate = datetime.datetime.now()
            page.product_counter = 0
            page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    @staticmethod
    def updt_inf_section(user_id, page_name, section_title, section_text):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            old_section_id = page_id + '-' + section_title
            old_section = InformativeSection.objects(id=old_section_id).first()
            if old_section:
                old_section.text = section_text
                old_section.save()
                page.lastModificationDate = datetime.datetime.now()
                page.save()
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    @staticmethod
    def get_page_sections(user_id, page_name) -> List[Document]:
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        print(page.name)
        print(page.id)
        print(page.sections)
        if page:
            expanded_sections = []
            for section in page.sections:
                expanded_sections.append(section)
            return expanded_sections
        else:
            raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")

    @classmethod
    def add_product(cls, user_id, page_name, sku, cant, title, desc, precio):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            collection = cls.get_instance()._db[page_id]
            if collection:
                product = collection.find_one({'key': sku})
                if product:
                    collection.update_one({"key": sku}, {"$set": {"stock": product["stock"] + cant, "name": title, "desc": desc, "price": precio}})
                else:
                    product = {
                        "key": sku,
                        "stock": cant,
                        "name": title,
                        "desc": desc,
                        "price": precio,
                    }
                    collection.insert_one(product)
        else:
            raise Exception("La pagina " + str(page) + " no existe o no te pertenece")

    @classmethod
    def set_product_multimedia(cls, user_id, page_name, product, media_url):
        page_id = user_id + '-' + page_name
        collection = cls.get_instance()._db[page_id]
        print("producto: ", product)
        print("imagen: ", media_url)
        if collection:
            producto = collection.find_one({"key": product})
            print("producto encontrado: ", producto)
            collection.update_one({"key": product}, {"$set": {"multimedia": media_url}})
            print("imagen seteada")
        else:
            print("no hay coleccion")

