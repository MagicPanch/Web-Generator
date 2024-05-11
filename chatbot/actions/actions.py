import threading
from generator.PageManager import PageManager
from generator.ReactGenerator import ReactGenerator
from generator.Front import Front
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import datetime
import os.path
import json
from database.DBManager import DBManager

#Actions Pagina
class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("----EN ACTION CREAR PAGINA----")
        if (tracker.get_slot('page_name') is None):
            dispatcher.utter_message(text="Repetime como queres que se llame tu página. Te recuerdo que el formato es: www. nombre-pagina .com")
            return []
        else:
            if (await DBManager.get_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name')) is None):
                # Crear back y front
                PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))] = [None, None]
                # Generator.running[(args[0], args[1])][0] = Back(args[0], args[1], PageManager.current_back_port)
                PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1] = Front(tracker.sender_id, tracker.get_slot('page_name'), PageManager.get_port(),
                                                                         "")  # running[(user, page_name)][0].get_app_adress())
                threading.Thread(target=PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].start_running_thread, args=(PageManager.create_project, (tracker.sender_id, tracker.get_slot('page_name')))).start()

                #PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].start_running_thread(target=PageManager.create_project, args=(tracker.sender_id, tracker.get_slot('page_name')))
                await DBManager.add_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), tracker.get_slot('usuario'), tracker.get_slot('tipo_seccion'))
                dispatcher.utter_message(text="Aguarda un momento mientras se crea tu página")
                return [SlotSet("page_name", tracker.get_slot('page_name')), FollowupAction("action_ejecutar_dev")]
            else:
                dispatcher.utter_message(text="Ya tenes una pagina con ese nombre. Elige otro")
                return []

class ActionEjecutarDev(Action):

    def name(self) -> Text:
        return "action_ejecutar_dev"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("----EN ACTION EJECUTAR DEV----")
        PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].join_running_thread()
        threading.Thread(target=PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].start_running_thread, args=(PageManager.run_dev, (tracker.sender_id, tracker.get_slot('page_name'), PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].page_port))).start()
        #PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].start_running_thread(target=PageManager.run_dev, args=(tracker.sender_id, tracker.get_slot('page_name'), PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].page_port))
        dispatcher.utter_message(text="Podes visualizar tu página en el siguiente link: " + PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].get_page_adress())
        return [FollowupAction("action_listen")]

class ActionEjecutarPagina(Action):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if (tracker.get_slot('page_name') is None):
            message = "Indicame el nombre de la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
            pags = await DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
            for pag in pags:
                message += str(pag['name']) + "\n"
        else:
            if (await DBManager.get_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name')) is None):
                message = "No se encuentra la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
                pags = await DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
                for pag in pags:
                    message += str(pag['name']) + "\n"
            else:
                if (not await DBManager.was_compiled(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'))):
                    threading.Thread(target=PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].start_running_thread, args=(PageManager.build, (tracker.sender_id, tracker.get_slot('page_name')))).start()
                else:
                    threading.Thread(target=PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].start_running_thread, args=(PageManager.run_project, (tracker.sender_id, tracker.get_slot('page_name'), PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].page_port))).start()
                    #PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].start_running_thread(target=PageManager.run_project, args=(tracker.sender_id, tracker.get_slot('page_name'), PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].page_port))
                message = "Puedes acceder a tu pagina en: " + PageManager.running_pages[(tracker.sender_id, tracker.get_slot('page_name'))][1].get_page_adress()
        dispatcher.utter_message(message)
        return []

    class ActionDetenerPagina(Action):

        def name(self) -> Text:
            return "action_detener_pagina"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            print("----EN ACTION DETENER PAGINA----")
            last_entities = tracker.latest_message.get("entities", None)
            print("last entities: " + str(last_entities))
            print("text: " + tracker.latest_message.get("text"))
            if last_entities is None:
                print("last_entities es None")
            else:
                print("last_entities no es None")
            if len(last_entities) == 0:
                if "todas" in tracker.latest_message.get("text"):
                    for pag in PageManager.get_running_user_pages(tracker.sender_id):
                        PageManager.stop_page(tracker.sender_id, pag.page_name)
                        print("------------PAGINA detenida---------")
                    message = "Tus paginas fueron apagadas con exito."
                else:
                    message = "Indicame el nombre de la pagina que deseas detener. Te recuerdo que tus paginas son: \n"
                    pags = PageManager.get_user_pages(tracker.sender_id)
                    for pag in pags:
                        message += str(pag) + "\n"
            elif "page_name" in (entity.keys() for entity in last_entities):
                PageManager.stop_page(tracker.sender_id, tracker.get_latest_entity_values('page_name'))
                print("------------PAGINA detenida---------")
                message = "Tu pagina fue apagada con exito."
            else:
                PageManager.stop_page(tracker.sender_id, tracker.get_slot('page_name'))
                print("------------PAGINA detenida---------")
                message = "Tu pagina fue apagada con exito."
            dispatcher.utter_message(message)
            return []

class ActionPreguntarTipoSeccion(Action):
    def name(self) -> Text:
        return "action_preguntar_tipo_seccion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = ("Que tipo de pagina queres? Algunos de los ejemplos que te podemos ofrecer son: \n" +
        "- E-Commerce \n" +
        "- Blog \n" +
        "- ABM \n" +
         "- Foro")
        dispatcher.utter_message(text=message)
        return [SlotSet("creando_seccion", True)]

class ActionGuardarSeccion(Action):

    def name(self) -> Text:
        return "action_guardar_seccion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("----EN GUARDAR SECCION----")
        tipo_seccion = next(tracker.get_latest_entity_values("seccion"), None)

        if(str(tipo_seccion))=="None" or tracker.get_intent_of_latest_message() == "despues_te_digo":
            message = "Bueno, podemos ver el tipo mas tarde"
        else:
            message = "Perfecto! Ya se guardo que tipo de sección quieres, la cual sera: \n" + str(tipo_seccion) + "."
        dispatcher.utter_message(text=str(message))
        dispatcher.utter_message(text="Aguarda un momento mientras se crea tu sección")
        return [SlotSet("tipo_seccion", tipo_seccion), FollowupAction("action_crear_seccion")]

class ActionCrearSeccion(Action):

    def name(self) -> Text:
        return "action_crear_seccion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("----EN CREAR SECCION----")
        page_path = PageManager.get_path(tracker.sender_id, tracker.get_slot('page_name'))
        dataSection = {}
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(tracker.sender_id)
        PageManager.go_to_dir(tracker.get_slot('page_name'))
        PageManager.go_to_dir("components")
        #ReactGenerator.generarSection(dataSection)
        print("-------------SECCION CREADA-------------")
        dispatcher.utter_message(text="Podes ver la nueva sección en tu página")
        return [SlotSet("creando_seccion", False)]

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
        slot_key = None
        if tracker.get_slot("creando_encabezado"):
            slot_key = "color_encabezado"
        if slot_key is not None:
            return [SlotSet(slot_key, color)]
        else:
            return []

class ActionRecibirImagen(Action):
    def name(self) -> Text:
        return "action_recibir_imagen"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
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
                        img_name = "logo-" + photo['file_unique_id']
                        await PageManager.download_telegram_image(PageManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), image_id=image_id, short_id=img_name)
            if not error:
                dispatcher.utter_message(text="Imagen recibida con éxito.")
            else:
                dispatcher.utter_message(text="No se pudo procesar la imagen.")
        else:
            if 'denegar' in latest_message:
                dispatcher.utter_message(text="Perfecto, el encabezado de tu página no contendrá ningún logo")
        return []

class ActionPreguntarColorEncabezado(Action):
    def name(self) -> Text:
        return "action_preguntar_color_encabezado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="De que color te gustaria que sea el encabezado?")
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
            "addressLogo": page_path + "\\img\\logo.png",
            "colorTitulo": "text-yellow-600"
        }
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(tracker.sender_id)
        PageManager.go_to_dir(tracker.get_slot('page_name'))
        PageManager.go_to_dir("components")
        ReactGenerator.generarHeader(dataHeader)
        print("-------------ENCABEZADO CREADO-------------")
        dispatcher.utter_message(text="Podes ver los cambios que realizamos en el encabezado")
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
        ide = tracker.sender_id
        message = "Hola " + nombre + ", como va tu " + horario + "? Soy el Chatbot WebGenerator, el encargado de ayudarte a crear tu pagina web! Si queres preguntame y te explico un poco en que cosas puedo contribuir."
        dispatcher.utter_message(text=str(message))

        print("en saludo telegram")
        await DBManager.add_user(DBManager.get_instance(), ide, tracker.get_slot("usuario"), nombre)
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
