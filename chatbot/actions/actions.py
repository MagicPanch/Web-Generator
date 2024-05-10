import threading
from random import random
import subprocess
from pymongo import MongoClient
from generator.Generator import Generator
from generator.Front import Front
import generator.GenericRoutes
import CONSTANTS
from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import datetime
import os.path
import json
from generator.DBManager import DBManager

#Actions Pagina
class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        creating_thread = threading.Thread(Generator.create_project(user=tracker.sender_id, page_name=tracker.get_slot('page_name')))
        creating_thread.start()
        creating_thread.join()
        #DBManager.add_user_page(user=tracker.sender_id, page_name=tracker.get_slot('page_name'))
        print("------------PAGINA CREADA---------")
        message = "Tu pagina fue creada con exito."
        dispatcher.utter_message(message)
        variable = next(tracker.get_latest_entity_values("page_name"), None)
        return [SlotSet("page_name", variable)]

class ActionEjecutarPagina(Action):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if (tracker.get_slot('page_name') is None):
            message = "Indicame el nombre de la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
            pags = Generator.get_user_pages(tracker.sender_id)
            for pag in pags:
                message += str(pag) + "\n"
        else:
            address = self.init_next_app(tracker.sender_id, tracker.get_slot('page_name'))
            print("------------PAGINA ejecutando---------")
            message = "Puedes acceder a tu pagina en: " + address
        dispatcher.utter_message(message)
        return []

    def init_next_app(self, user, page_name) -> str:

        # Crear back y front
        Generator.running[(user, page_name)] = [None, None]
        #Generator.running[(user, page_name)][0] = Back(user, page_name, Generator.current_back_port)
        Generator.running[(user, page_name)][1] = Front(user, page_name, Generator.current_front_port, "") #running[(user, page_name)][0].get_app_adress())

        # Incrementar puertos
        #Generator.inc_port(Generator.current_back_port, CONSTANTS.MAX_BACK_PORT)
        Generator.inc_port(Generator.current_front_port, CONSTANTS.MAX_FRONT_PORT)

        # Compilar
        Generator.running[(user, page_name)][1].build_page()
        print("------------PAGINA COMPILADA---------")

        # Iniciar la ejecucion de los hilos
        #running[(user, page_name)][0].start()
        Generator.running[(user, page_name)][1].start()
        # Agregar ruta
        #running[(user, page_name)][0].agregar_ruta('/get-producto', GenericRoutes.get_product, ['GET'])

        return Generator.running[(user, page_name)][1].get_page_adress()

    class ActionDetenerPagina(Action):

        def name(self) -> Text:
            return "action_detener_pagina"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            if (tracker.get_slot('page_name') is None):
                message = "Indicame el nombre de la pagina que deseas detener. Te recuerdo que tus paginas son: \n"
                pags = Generator.get_user_pages(tracker.sender_id)
                for pag in pags:
                    message += str(pag) + "\n"
            else:
                self.stop_next_app(tracker.sender_id, tracker.get_slot('page_name'))
                print("------------PAGINA detenida---------")
                message = "Tu pagina fue apagada con exito."
            dispatcher.utter_message(message)
            return []

        def stop_next_app(self, user, page_name):
            global current_back_port
            global current_front_port
            global running

            # Matar la página
            Generator.running[(user, page_name)][1].stop()

            Generator.running.pop((user, page_name))

            # Decrementar puertos
            Generator.dec_port(Generator.current_front_port, CONSTANTS.MIN_FRONT_PORT)

class ActionGuardaTipo(Action):

    def name(self) -> Text:
        return "action_guardar_tipo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tipo_pag = next(tracker.get_latest_entity_values("pagina"), None)

        if(str(tipo_pag))=="None":
            message = "Bueno, podemos ver el tipo mas tarde"
        else:
            message = "Perfecto! Ya se guardo que tipo de pagina quieres, la cual sera: \n" + str(tipo_pag) + "."
        dispatcher.utter_message(text=str(message))
        return [SlotSet("tipo_pagina", tipo_pag)]

# Saludo Actions
class ActionSaludoTelegram(Action):

    def name(self) -> Text:
        return "action_saludo_telegram"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        now = datetime.datetime.now()
        hora = int(now.strftime("%H"))
        if (hora > 0) and (hora <= 12):
            horario = "mañana"
        elif (hora > 12) and (hora <= 18):
            horario = "tarde"
        else:
            horario = "noche"
        variable = tracker.latest_message["metadata"]["message"]
        nombre = variable["from"]["first_name"]
        user_name = variable["from"]["username"]
        ide = variable["from"]["id"]
        message = "Hola " + nombre + ", como va tu " + horario + "? Soy el Chatbot WebGenerator, el encargado de ayudarte a crear tu pagina web! Si queres preguntame y te explico un poco en que cosas puedo contribuir."
        dispatcher.utter_message(text=str(message))
        return [SlotSet("usuario", user_name),SlotSet("horario", horario),SlotSet("id_user", ide)]

#Random Actions
class ActionDespedidaTelegram(Action):

    def name(self) -> Text:
        return "action_despedida_telegram"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        now = datetime.datetime.now()
        hora = now.strftime("%H")
        if (hora > "0") and (hora <= "12"):
            horario = "mañana"
        elif (hora > "12") and (hora <= "19"):
            horario = "tarde"
        else:
            horario = "noche"
        variable = tracker.latest_message["metadata"]["message"]
        nombre = variable["from"]["first_name"]
        message = "Que siga bien su " + horario + ", nos vemos " + nombre + "!!"
        dispatcher.utter_message(text=str(message))
        return []


# Action Devolver Hora
class ActionHora(Action):

    def name(self) -> Text:
        return "action_hora"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        now = datetime.datetime.now()
        dispatcher.utter_message("Hoy es " + now.strftime("%d/%m de 20%y"))
        hora = now.strftime("%H")
        if (hora > "2") and (hora <= "13"):
            dispatcher.utter_message("Y la hora es " + now.strftime("%H:%M") + " , tempranito ajaj")
        elif (hora > "13") and (hora <= "19"):
            dispatcher.utter_message("Y la hora es " + now.strftime("%H:%M") + " , hora de la siesta jajaj")
        else:
            dispatcher.utter_message("Y la hora es " + now.strftime("%H:%M") + " , medio tarde jaja")
        return []


# Estado de animo Action
class ActionAnimo(Action):

    def name(self) -> Text:
        return "action_animo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message['intent'].get('name')
        if (intent == "estado_de_animo_feliz"):
            SlotSet("animo", "Feliz")
            dispatcher.utter_message(template="utter_estado_de_animo_feliz")
        else:
            SlotSet("animo", "Triste")
            dispatcher.utter_message(template="utter_estado_de_animo_triste")
        return []


class ActionTriste(Action):

    def name(self) -> Text:
        return "action_triste"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        triste = tracker.latest_message['intent'].get('name')
        if str(triste) == 'triste_facu':
            dispatcher.utter_message(template="utter_triste_facu")
        else:
            dispatcher.utter_message(template="utter_triste_pelea")
        return []

# Json actions
class OperarArchivoDia():

    @staticmethod
    def guardar(AGuardar):
        with open(".\\actions\\dia", "w") as archivo_descarga:
            json.dump(AGuardar, archivo_descarga, indent=4)
        archivo_descarga.close()

    @staticmethod
    def cargarArchivo():
        if os.path.isfile(".\\actions\\dia"):
            with open(".\\actions\\dia", "r") as archivo_carga:
                retorno = json.load(archivo_carga)
                archivo_carga.close()
        else:
            retorno = {}
        return retorno


class OperarArchivoUser():

    @staticmethod
    def guardar(AGuardar):
        with open(".\\actions\\user", "w") as archivo_descarga:
            json.dump(AGuardar, archivo_descarga, indent=4)
        archivo_descarga.close()

    @staticmethod
    def cargarArchivo():
        if os.path.isfile(".\\actions\\user"):
            with open(".\\actions\\user", "r") as archivo_carga:
                retorno = json.load(archivo_carga)
                archivo_carga.close()
        else:
            retorno = {}
        return retorno


class ActionCrearUsuario(Action):
    def name(self) -> Text:
        return "action_crear_documento_usuario"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Conectarse a la base de datos MongoDB
        client = MongoClient(
            'mongodb+srv://design:label123@cluster0.3yowbc8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0',
            27017)  # cambiar localhost por url propio
        db = client['web_generator']
        usuarios = db['users']

        # Extraer la información del tracker de la conversación
        ide = tracker.get_slot("id_user")
        username = tracker.get_slot("usuario")

        # Verificar si el usuario ya existe en la base de datos
        existing_user = usuarios.find_one({"_id": ide})
        if existing_user:
            dispatcher.utter_message("¡El usuario ya existe en MongoDB!")
        else:
            # Crear un documento para insertar en la colección
            nuevo_usuario = {
                "_id": ide,
                "username": username,
                "paginas": []  # nueva subcoleccion de paginas creadas vacia
            }
            # Insertar el documento en la colección
            usuarios.insert_one(nuevo_usuario)
            dispatcher.utter_message("¡Nuevo usuario ingresado en MongoDB!")

        # Cerrar la conexión con MongoDB
        client.close()

        return []

class ActionAgregarPagina(Action):

    def name(self) -> Text:
        return "action_crear_documento_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Conectarse a la base de datos MongoDB
        client = MongoClient('mongodb+srv://design:label123@cluster0.3yowbc8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0',27017)  # cambiar localhost por url propio
        db = client['web_generator']
        usuarios = db['users']
        # Buscar el usuario por su ID
        usuario = usuarios.find_one({'_id': tracker.get_slot("id_user")})
        if usuario:
            # Crear el documento de la nueva página
            nueva_pagina = {
                'id': random()*100, #pagina_info.get('id', ''),  # ID de la página
                'nombre': tracker.get_slot("page_name"), #pagina nombre
                'contact':  tracker.get_slot("usuario"), #pagina_info.get('contact', ''),  # Información de contacto
                'creationDate': datetime.datetime.utcnow(),  # Fecha de creación (actual)
                'lastModification': datetime.datetime.now(),  # Última fecha de modificación (actual)
                'compilada': False, #pagina_info.get('compilada', False),
                # Indicador de compilación (predeterminado: False)
                'webType': tracker.get_slot("tipo_pagina") #pagina_info.get('webType', '')  # Tipo de página web
            }
            # Agregar la nueva página a la subcolección 'paginas' del usuario
            usuarios.update_one(
                {'_id': tracker.get_slot("id_user")},
                {'$push': {'paginas': nueva_pagina}}
            )
            dispatcher.utter_message("Página agregada correctamente.")
        else:
            dispatcher.utter_message("Usuario no encontrado")
        # Cerrar la conexión con la base de datos al finalizar
        client.close()
        dispatcher.utter_message("¡Nueva pagina ingresada en MongoDB!")
        return [SlotSet("tipo_pagina", None)]

class ActionRobotScrapper(Action):

    def name(self) -> Text:
        return "action_robot_scrapper"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        def ejecutar_bat(ruta_bat):
            subprocess.call(ruta_bat, shell=True)

        # Ejemplo de uso
        ruta_bat = "C:\Eclipse-TUDAI\Virtual1\EjecucionBat.bat"
        ejecutar_bat(ruta_bat)
        return[]