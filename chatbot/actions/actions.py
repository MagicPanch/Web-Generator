import threading

import CONSTANTS
from generator.PageManager import PageManager
from generator.ReactGenerator import ReactGenerator
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

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR PAGINA----")

        if tracker.get_slot('page_name') is None:
            dispatcher.utter_message(
                text="Repetime como queres que se llame tu página. Te recuerdo que el formato es: www. nombre-pagina .com")
            return []
        else:
            if DBManager.get_page_by_name(DBManager.get_instance(), tracker.get_slot('page_name')) is None:
                #La pagina no existe

                #Se crea la entrada para la pagina en PageManager
                PageManager.add_page(tracker.sender_id, tracker.get_slot('page_name'))

                #Se crea en un nuevo hilo el proyecto de la pagina
                PageManager.create_project(tracker.sender_id, tracker.get_slot('page_name'))

                #Se guarda su entrada en la base de datos
                DBManager.add_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'),
                                   tracker.get_slot('usuario'), tracker.get_slot('tipo_seccion'))

                #Se copia el template al nuevo proyecto
                #PageManager.copy_template(tracker.sender_id, tracker.get_slot('page_name'))

                dispatcher.utter_message(text="Aguarda un momento mientras se crea tu página.")
                return [FollowupAction("action_ejecutar_dev")]
            else:
                #La pagina ya existe
                dispatcher.utter_message(text="Ya existe una pagina con ese nombre. Por favor elige otro.")
                return []


class ActionEjecutarDev(Action):

    def name(self) -> Text:
        return "action_ejecutar_dev"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR DEV----")
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))

        #Se espera a que el hilo de creación finalice
        PageManager.join_thread(page.get_user(), page.get_name())

        #Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
        PageManager.run_dev(page.get_user(), page.get_name())

        page_address = page.get_page_address()
        print("(" + threading.current_thread().getName() + ") " + "--------page_address: ", page_address)
        dispatcher.utter_message(text="Podes visualizar tu página en el siguiente link: " + page_address)
        return []


class ActionEjecutarPagina(Action):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot('page_name') is None:
            #No hay contexto de ninguna pagina en especial

            message = "Indicame el nombre de la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
            pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
            for pag in pags:
                message += str(pag['name']) + "\n"
        else:
            #Se estuvo hablando de una pagina en particular

            if DBManager.get_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name')) is None:
                #Esa pagina no pertenece al usuario
                message = "No se encuentra la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
                pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
                for pag in pags:
                    message += str(pag['name']) + "\n"
            else:
                #La pagina pertenece al usuario

                page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))
                if DBManager.was_compiled(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name')):
                    #Hay que compilarla

                    # Verificar si la pagina está ejecutando
                    if page.is_running():
                        PageManager.stop_page(tracker.sender_id, tracker.get_slot('page_name'))

                    #Esperar a que el hilo de ejecución finalice si está ejecutando
                    PageManager.join_thread(page.get_user(), page.get_name())

                    # Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
                    PageManager.build_project(page.get_user(), page.get_name())
                #Se ejecuta

                # Esperar a que el hilo de ejecución finalice si está ejecutando
                PageManager.join_thread(page.get_user(), page.get_name())

                # Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
                PageManager.run_project(page.get_user(), page.get_name())
                page_address = page.get_page_address()
                message = "Puedes acceder a tu pagina en: " + page_address
        dispatcher.utter_message(message)
        return []

    class ActionDetenerPagina(Action):

        def name(self) -> Text:
            return "action_detener_pagina"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[
            Dict[Text, Any]]:
            last_entities = tracker.latest_message.get("entities", None)
            if len(last_entities) == 0:
                #No se especifico ninguna pagina

                if "todas" in tracker.latest_message.get("text"):
                    #Quiere detener todas

                    for pag in PageManager.get_user_running_pages(tracker.sender_id):
                        PageManager.stop_page(tracker.sender_id, pag.get_name())
                        print("------------PAGINA detenida---------")
                    message = "Tus paginas fueron apagadas con exito."
                else:
                    #Quiere detener una en particular

                    message = "Indicame el nombre de la pagina que deseas detener. Te recuerdo que tus paginas en ejecución son: \n"
                    pags = PageManager.get_user_running_pages(tracker.sender_id)
                    for pag in pags:
                        message += str(pag.get_name()) + "\n"
            elif "page_name" in (entity.keys() for entity in last_entities):
                # Se especifico una pagina en el ultimo mensaje

                PageManager.stop_page(tracker.sender_id, tracker.get_latest_entity_values('page_name'))
                print("------------PAGINA detenida---------")
                message = "Tu pagina fue apagada con exito."
            else:
                #Se detiene la ultima pagina de la que se hablo anteriormente

                PageManager.stop_page(tracker.sender_id, tracker.get_slot('page_name'))
                print("------------PAGINA detenida---------")
                message = "Tu pagina fue apagada con exito."
            dispatcher.utter_message(message)
            return []

class ActionCapturarComponenteEdicion(Action):

    def name(self) -> Text:
        return "action_capturar_componente_edicion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EDICION COMPONENTE----")
        componente = tracker.get_slot('componente')
        print("(" + threading.current_thread().getName() + ") " + "--------componente: ", componente)
        if not componente:
            #No se especifico el componente a editar
            message = "Que componente quisieras editar? Te recuerdo que los componentes son: \n"
            message += "Encabezado \n"
            message += "Footer \n"
            dispatcher.utter_message(text=message)
        elif componente == "encabezado":
            return[FollowupAction("action_preguntar_color_encabezado")]
        elif componente == "footer":
            return[FollowupAction("action_preguntar_mail_footer")]
        else:
            return[FollowupAction("action_default_fallback")]


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

        if (str(tipo_seccion)) == "None" or tracker.get_intent_of_latest_message() == "despues_te_digo":
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
        page_path = PageManager.get_page_path(tracker.sender_id, tracker.get_slot('page_name'))
        dataSection = {}
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

        if (str(color)) == "None" or tracker.get_intent_of_latest_message() == "despues_te_digo":
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
            photo = latest_message['metadata']['message']['photo'][1]
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
        page_path = PageManager.get_page_path(tracker.sender_id, tracker.get_slot('page_name'))
        print(page_path)
        dataHeader = {
            "titulo": tracker.get_slot('page_name'),
            "address": page_path,
            "addressLogo": "./logo.png",
            "colorTitulo": "text-yellow-600"
        }
        ReactGenerator.generarHeader(dataHeader)
        print("-------------ENCABEZADO MODIFICADO-------------")
        dispatcher.utter_message(text="Podes ver los cambios que realizamos en el encabezado")
        return [SlotSet("creando_encabezado", False)]


class ActionPreguntarMailFooter(Action):
    def name(self) -> Text:
        return "action_preguntar_mail_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTAR MAIL FOOTER----")
        dispatcher.utter_message(text="Queres cambiar tu e-mail en el footer?")
        return [SlotSet("creando_footer", True)]

class ActionGuardarMailFooter(Action):
    def name(self) -> Text:
        return "action_guardar_mail_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION GUARDAR MAIL FOOTER----")
        latest_message = tracker.latest_message
        if 'mail' in latest_message:
        #El usuario proporciono el mail
            mail = str(tracker.get_slot("mail"))
            #Guardar el mail en la pagina
            DBManager.set_page_mail(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), mail)
            dispatcher.utter_message(text="E-mail guardado.")
            return [SlotSet("mail_footer", mail), FollowupAction("utter_preguntar_ubicacion")]
        elif 'denegar' in latest_message:
        #El usuario no quiere modificar el mail
            dispatcher.utter_message(text="Perfecto, no se modificara el mail mostrado en el footer de su pagina.")
            return [FollowupAction("utter_preguntar_ubicacion")]
        else:
            return [FollowupAction("action_default_fallback")]

class ActionGuardarUbicacionFooter(Action):
    def name(self) -> Text:
        return "action_guardar_ubicacion_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION GUARDAR UBICACION FOOTER----")
        latest_message = tracker.latest_message
        if 'ubicacion' in latest_message:
        #El usuario proporciono su ubicacion
            ubicacion = str(tracker.get_slot("ubicacion"))
            #Guardar la ubicacion en la pagina
            DBManager.set_page_location(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), ubicacion)
            dispatcher.utter_message(text="Ubicacion guardada.")
            return [SlotSet("ubicacion_footer", ubicacion)]
        elif 'denegar' in latest_message:
        #El usuario no quiere modificar el mail
            dispatcher.utter_message(text="Perfecto, no se modificara la ubicacion mostrada en el footer de su pagina.")
            return []
        else:
            return [FollowupAction("action_default_fallback")]

class ActionCrearFooter(Action):
    def name(self) -> Text:
        return "action_crear_Footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR FOOTER----")
        page_path = PageManager.get_page_path(tracker.sender_id, tracker.get_slot('page_name'))
        mail = str(tracker.get_slot("mail_footer"))
        if not mail:
            mail = "contactDesignLabel@gmail.com"
        ubicacion = str(tracker.get_slot("ubicacion_footer"))
        if not ubicacion:
            ubicacion = "Pinto 401 Tandil, Argentina"
        dataFooter = {
            "address": page_path,
            "email": mail,
            "ubicacion": ubicacion
        }
        ReactGenerator.generarFooter(dataFooter)
        print("-------------FOOTER MODIFICADO-------------")
        dispatcher.utter_message(text="Podes ver los cambios que realizamos en el footer")
        return [SlotSet("creando_encabezado", False)]


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
        user_name = variable["from"].get("user_name", None)
        ide = tracker.sender_id
        message = "Hola " + nombre + ", como va tu " + horario + "? Soy el Chatbot WebGenerator, el encargado de ayudarte a crear tu pagina web! Si queres preguntame y te explico un poco en que cosas puedo contribuir."
        dispatcher.utter_message(text=str(message))

        print("en saludo telegram")
        DBManager.add_user(DBManager.get_instance(), ide, tracker.get_slot("usuario"), nombre)
        print("----FINALIZA SALUDO TELEGRAM----")

        return [SlotSet("usuario", user_name), SlotSet("horario", horario), SlotSet("id_user", ide)]


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
        if intent == "estado_de_animo_feliz":
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
