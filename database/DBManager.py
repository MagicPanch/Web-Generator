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

    def add_page(self, user_id, page_name, contact):
        user = User.objects(id=user_id).first()
        if user:
            page_id = user_id + '-' + page_name
            sections[] #se crea la pagina sin secciones hasta que el usuario decida agregar alguna
            page = Page(id=page_id, name=page_name, contact=contact, creationDate=datetime.datetime.utcnow(), lastModificationDate=datetime.datetime.now(), sections=sections)
            page.save()
            user.paginas.append(page)
            user.save()
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")
    
    def add_informative_section(self, user_id, page_name, section_name, multimedia, text):
        user = User.objects(id=user_id).first()
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if user:
            if page:
                section_id = user_id + '-' + page_name + '-' + section_name #id unico de cada seccion
                section = informativeSection(id=section_id, multimedia=multimedia, text=text)
                section.save()
                page.sections.append(section) 
                page.lastModificationDate = datetime.now()
                page.save()
            else:
                raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")
    
    def add_catalogue_section(self, user_id, page_name, contact, section_name, product): #product es un array de referencias al esquema Product
        user = User.objects(id=user_id).first()
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if user:
            if page:
                section_id = user_id + '-' + page_name + '-' + section_name #id unico de cada seccion
                section = Section(id=section_id, product=product)
                section.save()
                page.sections.append(section) 
                page.lastModificationDate = datetime.now()
                page.save()
            else:
                raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")

    def add_shop_section(self, user_id, page_name, contact, section_name, images, cart, section_filter, product, browser):
        user = User.objects(id=user_id).first()
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if user:
            if page:
                section_id = user_id + '-' + page_name + '-' + section_name #id unico de cada seccion
                section = Section(id=section_id, images=images, cart=cart, filter=section_filter, product=product, browser=browser)
                section.save()
                page.sections.append(section) 
                page.lastModificationDate = datetime.now()
                page.save()
            else:
                raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")

    def add_product(self, user_id, page_name, section_name, product)
        user = User.objects(id=user_id).first()
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if user:
            if page:
                section_id = user_id + '-' + page_name '-' + section_name
                section = ShopSection.objects(id=section_id).first()
                if section:
                    product.save()
                    section.product.append(product)
                    section.save()
                    user.page.lastModificationDate = datetime.now()
                    page.save()
                else:
                    raise Exception("La sección " + str(section_name) + " no existe o no te pertenece")
            else:
                raise Exception("La pagina " + str(page_name) + " no existe o no te pertenece")
        else:
            raise Exception("El usuario " + str(user_id) + " no existe")

    def get_product(self, user_id, page_id, section_id, product_id):
        product = Product.objects(id=page_id).first()
        if product:
            return product
        else:
            return None

    def get_page(self, user_id, page_name):
        page_id = user_id + '-' + page_name
        page = Page.objects(id=page_id).first()
        if page:
            return page
        else:
            return None

    def get_section(self, user_id, page_name, section_name):
        section_id = user_id + '-' + page_name + '-' + section_name
        section = Section.objects(id=section_id).first()
        if section:
            return section
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
            print("page.name", page.name)
            print("page.compilationDate", page.compilationDate)
            print("page.lastModificationDate", page.lastModificationDate)

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