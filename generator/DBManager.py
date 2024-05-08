import datetime
import threading
from pymongo.mongo_client import MongoClient
import CONSTANTS

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
        else:
            raise Exception("No se puede crear otra instancia de DB Manager")

    async def add_user(self, id, username):
        db = self._client['web_generator']
        usuarios = db['users']
        if not usuarios.find_one({"_id": id}):
            await usuarios.insert_one(
                {
                    "_id": id,
                    "username": username,
                    "paginas": []  # nueva subcoleccion de paginas creadas vacia
                })
            print("----USUARIO INSERTADO EN LA DB----")
        else:
            print("----USUARIO YA EXISTENTE EN LA DB----")

    async def add_page(self, user_id, page_name, contact, webType):
        db = self._client['web_generator']
        usuarios = db['users']
        usuario = usuarios.find_one({'_id': int(user_id)})
        if usuario:
            nueva_pagina = {
                '_id': user_id + '-' + page_name,
                'nombre': page_name,
                'contact': contact,
                'creationDate': datetime.datetime.utcnow(),  # Fecha de creación (actual)
                'lastModification': datetime.datetime.now(),  # Última fecha de modificación (actual)
                'compilada': False,
                'webType': webType
            }
            #Cuando se cree la colección de páginas
            '''
            paginas = db['pages']
            if not paginas.find_one({"_id": nueva_pagina["id"]}):
                await paginas.insert_one(nueva_pagina)
                await usuarios.update_one(
                {'_id': user_id},
                {'$push': {'paginas': nueva_pagina}})
            else:
                raise Exception("El usuario" + str(user_id) + " ya tiene una pagina con este nombre (" + str(page_name) + ")")
            '''
        else:
            raise Exception("El usuario " + user_id + " no existe")

    async def was_compiled(self, user_id, page_name):
        db = self._client['web_generator']
        #Cuando se cree la colección de páginas
        '''
        paginas = db['pages']
        return await paginas.find_one({"_id": str(user_id) + "-" + str(page_name), "compilada": True})
        '''
        return False