from generator.PageManager import PageManager
from generator.ReactGenerator import ReactGenerator
from generator.Front import Front
import CONSTANTS
from typing import Any, Text, Dict, List
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

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Aguarda un momento mientras se crea tu página")
        PageManager.start_running_thread(target=PageManager.create_project, args=(tracker.sender_id, tracker.get_slot('page_name')))

        await DBManager.add_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), tracker.get_slot('usuario'), tracker.get_slot('tipo_pagina'))
        print("------------PAGINA GUARDADA EN DB---------")

        return [SlotSet("page_name", tracker.get_slot('page_name'))]

class ActionEjecutarPagina(Action):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if (tracker.get_slot('page_name') is None):
            message = "Indicame el nombre de la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
            pags = PageManager.get_user_pages(tracker.sender_id)
            for pag in pags:
                message += str(pag) + "\n"
        else:
            address = await self.init_next_app(tracker.sender_id, tracker.get_slot('page_name'))
            print("------------PAGINA ejecutando---------")
            message = "Puedes acceder a tu pagina en: " + address
        dispatcher.utter_message(message)
        return []

    async def init_next_app(self, user, page_name) -> str:

        # Crear back y front
        PageManager.running_pages[(user, page_name)] = [None, None]
        #Generator.running[(user, page_name)][0] = Back(user, page_name, Generator.current_back_port)
        PageManager.running_pages[(user, page_name)][1] = Front(user, page_name, PageManager.current_front_port, "") #running[(user, page_name)][0].get_app_adress())

        # Incrementar puertos
        #Generator.inc_port(Generator.current_back_port, CONSTANTS.MAX_BACK_PORT)
        PageManager.inc_port(PageManager.current_front_port, CONSTANTS.MAX_FRONT_PORT)

        # Compilar
        if (not await DBManager.was_compiled(DBManager.get_instance(), user, page_name)):
            PageManager.running_pages[(user, page_name)][1].build()
            print("------------PAGINA COMPILADA---------")
        else:
            print("------------PAGINA YA COMPILADA---------")

        # Iniciar la ejecucion de los hilos
        #running[(user, page_name)][0].start()
        PageManager.running_pages[(user, page_name)][1].start()
        # Agregar ruta
        #running[(user, page_name)][0].agregar_ruta('/get-producto', GenericRoutes.get_product, ['GET'])

        return PageManager.running_pages[(user, page_name)][1].get_page_adress()

    class ActionDetenerPagina(Action):

        def name(self) -> Text:
            return "action_detener_pagina"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            if (tracker.get_slot('page_name') is None):
                message = "Indicame el nombre de la pagina que deseas detener. Te recuerdo que tus paginas son: \n"
                pags = PageManager.get_user_pages(tracker.sender_id)
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
            PageManager.running[(user, page_name)][1].stop()
            PageManager.running.pop((user, page_name))

            # Decrementar puertos
            PageManager.dec_port(PageManager.current_front_port, CONSTANTS.MIN_FRONT_PORT)

class ActionGuardarTipo(Action):

    def name(self) -> Text:
        return "action_guardar_tipo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tipo_pag = next(tracker.get_latest_entity_values("pagina"), None)

        if(str(tipo_pag))=="None" or tracker.get_intent_of_latest_message() == "despues_te_digo":
            message = "Bueno, podemos ver el tipo mas tarde"
        else:
            message = "Perfecto! Ya se guardo que tipo de pagina quieres, la cual sera: \n" + str(tipo_pag) + "."
        dispatcher.utter_message(text=str(message))
        return [SlotSet("tipo_pagina", tipo_pag)]

class ActionGuardarColor(Action):
    def name(self) -> Text:
        return "action_guardar_color"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        color = next(tracker.get_latest_entity_values("color"), None)
        #text - yellow - 600

        if (str(color))=="None" or tracker.get_intent_of_latest_message() == "despues_te_digo":
            message = "Bueno, podemos ver el tipo mas tarde"
        else:
            message = "Perfecto! Ya se guardo que color queres, el cual sera: \n" + str(color) + "."
        dispatcher.utter_message(text=str(message))
        if tracker.get_slot("creando_encabezado"):
            slot_key = "color_encabezado"
        return [SlotSet(slot_key, color)]

class ActionRecibirImagen(Action):
    def name(self) -> Text:
        return "action_recibir_imagen"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        PageManager.join_running_thread()

        # Verifica si el último mensaje contiene una imagen
        latest_message = tracker.latest_message
        if 'photo' in latest_message['metadata']['message']:
            error = False
            for photo in latest_message['metadata']['message']['photo']:
                image_id = photo['file_id']
                if not image_id:
                    error = True
                else:
                    if tracker.get_slot("creando_encabezado"):
                        img_name = "logo"
                    await PageManager.download_telegram_image(PageManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), image_id=image_id, short_id=img_name)
            if not error:
                dispatcher.utter_message(text="Imagen recibida con éxito.")
            else:
                dispatcher.utter_message(text="No se pudo procesar la imagen.")
        else:
            if 'denegar' in latest_message:
                dispatcher.utter_message(text="Perfecto, el encabezado de tu página no contendrá ningún logo")
        return []

class ActionCreandoEncabezado(Action):
    def name(self) -> Text:
        return "action_creando_encabezado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet("creando_encabezado", True)]

class ActionCrearEncabezado(Action):
    def name(self) -> Text:
        return "action_crear_encabezado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        page_path = PageManager.get_path(tracker.sender_id, tracker.get_slot('page_name'))
        dataHeader = {
            "titulo": tracker.get_slot('page_name'),
            "address": page_path,
            "addressLogo": page_path + "\\logo.png",
            "colorTitulo": "text-yellow-600"
        }
        ReactGenerator.generarHeader(dataHeader)
        print("-------------ENCABEZADO CREADO-------------")
        return [SlotSet("creando_encabezado", False)]

    # Saludo Actions
class ActionSaludoTelegram(Action):

    def name(self) -> Text:
        return "action_saludo_telegram"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
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
        user_name = variable["from"].get("user_name", None)
        ide = variable["from"]["id"]
        message = "Hola " + nombre + ", como va tu " + horario + "? Soy el Chatbot WebGenerator, el encargado de ayudarte a crear tu pagina web! Si queres preguntame y te explico un poco en que cosas puedo contribuir."
        dispatcher.utter_message(text=str(message))

        await DBManager.add_user(DBManager.get_instance(), tracker.get_slot("id_user"), tracker.get_slot("usuario"))
        print("----FINALIZA SALUDO TELEGRAM----")

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
