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
class ActionPreguntarNombrePagina(Action):

    def name(self):
        return "action_preguntar_nombre_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTAR NOMBRE PAGINA----")
        dispatcher.utter_message(text="¿Como queres que se llame tu pagina? Por favor indica su nombre en el siguiente formato: www. nombre-pagina .com")
        return [SlotSet("creando_pagina", True)]

class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR PAGINA----")

        if tracker.get_slot('page_name') is None:
            dispatcher.utter_message(
                text="Repetime como queres que se llame tu página. Te recuerdo que el formato es: www. nombre-pagina .com")
            return [SlotSet("creando_pagina", True)]
        else:
            if DBManager.get_page_by_name(DBManager.get_instance(), tracker.get_slot('page_name')) is None:
                #La pagina no existe

                #Se crea la entrada para la pagina en PageManager
                PageManager.add_page(tracker.sender_id, tracker.get_slot('page_name'))

                #Se crea en un nuevo hilo el proyecto de la pagina
                PageManager.create_project(tracker.sender_id, tracker.get_slot('page_name'))

                #Se guarda su entrada en la base de datos
                DBManager.add_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), tracker.get_slot('usuario'))

                dispatcher.utter_message(text="Aguarda un momento mientras se crea tu página.")
                return [FollowupAction("action_ejecutar_dev"), SlotSet("creando_pagina", False)]
            else:
                #La pagina ya existe
                dispatcher.utter_message(text="Ya existe una pagina con ese nombre. Por favor elige otro.")
                return [SlotSet("creando_pagina", True)]

class ActionModificarPagina(Action):

    def name(self) -> Text:
        return "action_modificar_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION MODIFICAR PAGINA----")

        if tracker.get_slot('page_name') is None:
            message = "Indicame el nombre de la pagina que deseas modificar. Te recuerdo que tus paginas son: \n"
            pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
            for pag in pags:
                message += str(pag['name']) + "\n"
            dispatcher.utter_message(text=message)
            return [SlotSet("pregunta_modificacion", True)]
        else:
            # Se estuvo hablando de una pagina en particular
            page_doc = DBManager.get_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'))
            if not page_doc:
                # Esa pagina no pertenece al usuario
                message = "No se encuentra la pagina que deseas ejecutar. Te recuerdo que tus paginas son: \n"
                pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
                for pag in pags:
                    message += pag.name + "\n"
                dispatcher.utter_message(text=message)
                return [SlotSet("pregunta_modificacion", True)]
            else:
            # La pagina pertenece al usuario
                # Verificar si la pagina está viva
                page_obj = PageManager.get_page(tracker.sender_id, page_doc.name)
                if page_obj:
                    # La pagina esta viva
                    if page_obj.is_running():
                        # La pagina está ejecutando
                        PageManager.stop_page(tracker.sender_id, page_doc.name)
                return [SlotSet("pregunta_modificacion", False), FollowupAction("action_ejecutar_dev")]


class ActionEjecutarDev(Action):

    def name(self) -> Text:
        return "action_ejecutar_dev"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR DEV----")
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))

        #Se espera a que el hilo finalice
        PageManager.join_thread(page.get_user(), page.get_name())

        #Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
        PageManager.run_dev(page.get_user(), page.get_name())

        page_address = page.get_page_address()
        print("(" + threading.current_thread().getName() + ") " + "--------page_address: ", page_address)
        dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_address)
        return []


class ActionEjecutarPagina(Action):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR PAGINA----")

        if tracker.get_slot('page_name') is None:
            message = "Indicame el nombre de la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
            pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
            for pag in pags:
                message += str(pag['name']) + "\n"
            return [SlotSet("pregunta_ejecucion", True)]
        else:
            # Se estuvo hablando de una pagina en particular
            page_doc = DBManager.get_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'))
            print("(" + threading.current_thread().getName() + ") " + "--------page_doc: ", page_doc)
            if not page_doc:
                # Esa pagina no pertenece al usuario
                message = "No se encuentra la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
                pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
                for pag in pags:
                    message += str(pag['name']) + "\n"
                dispatcher.utter_message(text=message)
                return [SlotSet("pregunta_ejecucion", True)]
            else:
            # La pagina pertenece al usuario
                page_obj = PageManager.get_page(tracker.sender_id, page_doc.name)
                if page_obj:
                # La pagina esta viva
                    if page_obj.is_running():
                    # Verificar si la pagina está ejecutando
                        dispatcher.utter_message(text="Tu pagina ya esta ejecutando. Puedes acceder a ella en el siguiente link: " + PageManager.get_page(tracker.sender_id, page_doc.name).get_page_address())
                        return []
                    else:
                    # Se esta ejecutando en modo dev
                        PageManager.stop_page(tracker.sender_id, page_doc.name)
                        page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)
                        print("(" + threading.current_thread().getName() + ") " + "------------page_obj: ", page_obj)
                else:
                # La pagina no vive en PageManager
                    page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)

                #Verificar si esta compilada
                if not DBManager.was_compiled(DBManager.get_instance(), tracker.sender_id, page_doc.name):
                    print("(" + threading.current_thread().getName() + ") " + "----------------pagina no compilada")
                    PageManager.build_project(tracker.sender_id, page_doc.name)
                    DBManager.set_compilation_date(DBManager.get_instance(), tracker.sender_id, page_doc.name)
                    PageManager.join_thread(tracker.sender_id, page_doc.name)
                    print("(" + threading.current_thread().getName() + ") " + "------------PAGINA COMPILADA")
                else:
                    print("(" + threading.current_thread().getName() + ") " + "----------------pagina ya compilada")

                # Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
                PageManager.run_project(tracker.sender_id, page_doc.name)

                page_address = page_obj.get_page_address()
                print("(" + threading.current_thread().getName() + ") " + "------------page_address: ", page_address)
                dispatcher.utter_message(text="Podes acceder a tu página en el siguiente link: " + page_address)
                return [SlotSet("pregunta_ejecucion", False)]

    class ActionDetenerPagina(Action):

        def name(self) -> Text:
            return "action_detener_pagina"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            print("(" + threading.current_thread().getName() + ") " + "----ACTION DETENER PAGINA----")
            last_message_entities = tracker.get_latest_entity_values("text")
            print("(" + threading.current_thread().getName() + ") " + "--------last_message_entities: ", last_message_entities)

            if "page_name" in last_message_entities:
                # Se especifico una pagina en el ultimo mensaje

                PageManager.stop_page(tracker.sender_id, tracker.get_latest_entity_values('page_name'))
                print("(" + threading.current_thread().getName() + ") " + "------------PAGINA DETENIDA CON EXITO------------")
                dispatcher.utter_message(text="Tu pagina fue apagada con exito.")
            elif "todas" in tracker.latest_message.get("text"):
                # Quiere detener todas

                for pag in PageManager.get_user_running_pages(tracker.sender_id):
                    PageManager.stop_page(tracker.sender_id, pag.get_name())
                    dispatcher.utter_message(text="La pagina " + pag.get_name() + " fue detenida con éxito.")
                print("(" + threading.current_thread().getName() + ") " + "------------PAGINAS DETENIDA CON EXITO------------")
            else:
                #No especifico cual quiere detener pero hay slot de contexto
                page_name = tracker.get_slot('page_name')
                if page_name:
                    PageManager.stop_page(tracker.sender_id, page_name)
                    print("(" + threading.current_thread().getName() + ") " + "------------PAGINA DETENIDA CON EXITO------------")
                    dispatcher.utter_message(text="Tu pagina fue apagada con exito.")
                else:
                    message = "Indicame el nombre de la pagina que deseas detener. Te recuerdo que tus paginas en ejecución son: \n"
                    pags = PageManager.get_user_running_pages(tracker.sender_id)
                    for pag in pags:
                        message += str(pag.get_name()) + "\n"
                    dispatcher.utter_message(message)
                    return [SlotSet("pregunta_ejecucion", True)]
            return []

class ActionCapturarEdicion(Action):

    def name(self) -> Text:
        return "action_capturar_edicion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EDICION COMPONENTE----")
        componente = tracker.get_slot('componente')
        page_name = tracker.get_slot('page_name')
        if page_name and componente:
        # Hay pagina y componente a editar
            print("(" + threading.current_thread().getName() + ") " + "--------componente: ", componente)
            print("(" + threading.current_thread().getName() + ") " + "--------pagina: ", page_name)

            page_doc = DBManager.get_page(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'))
            print("(" + threading.current_thread().getName() + ") " + "--------page_doc: ", page_doc)
            if not page_doc:
                # Esa pagina no pertenece al usuario
                message = "La pagina que estas intentando modificar no te pertenece. Te recuerdo que tus paginas son: "
                pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
                for pag in pags:
                    message += str(pag.name) + "\n"
                dispatcher.utter_message(text=message)
                return [SlotSet("pregunta_nombre", True)]
            else:
                # La pagina pertenece al usuario
                print("(" + threading.current_thread().getName() + ") " + "------------la pagina es del usuario")
                page_obj = PageManager.get_page(tracker.sender_id, page_doc.name)
                if page_obj:
                    # La pagina esta viva
                    print("(" + threading.current_thread().getName() + ") " + "----------------la pagina esta viva")
                    print("(" + threading.current_thread().getName() + ") " + "------------page_obj: ", page_obj)
                    PageManager.stop_page(tracker.sender_id, page_doc.name)
                    print("(" + threading.current_thread().getName() + ") " + "----------------pagina_detenida")
                else:
                    # La pagina no vive en PageManager
                    print("(" + threading.current_thread().getName() + ") " + "----------------la pagina NO esta viva")
                page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)
                print("(" + threading.current_thread().getName() + ") " + "--------page_obj: ", page_obj)
                PageManager.run_dev(tracker.sender_id, page_doc.name)
                page_address = page_obj.get_page_address()
                dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_address)
                if componente == "encabezado":
                    return[FollowupAction("action_preguntar_color_encabezado"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                elif componente == "footer":
                    return[FollowupAction("action_preguntar_mail_footer"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]

        elif page_name and not componente:
        # Hay pagina y no hay componente a editar
            print("(" + threading.current_thread().getName() + ") " + "--------pagina: ", page_name)
            message = "Que componente quisieras editar? Te recuerdo que los componentes son: \n"
            message += "Encabezado \n"
            message += "Footer \n"
            dispatcher.utter_message(text=message)
            return [SlotSet("pregunta_componente", True)]

        elif not page_name and componente:
        # No hay pagina y hay componente a editar
            print("(" + threading.current_thread().getName() + ") " + "--------componente: ", componente)
            message = "Indicame el nombre de la pagina que deseas modificar. Te recuerdo que tus paginas son: \n"
            pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
            for pag in pags:
                message += str(pag.name) + "\n"
            dispatcher.utter_message(text=message)
            return [SlotSet("pregunta_nombre", True)]
        else:
        # No hay pagina ni componente
            message = "Indicame el nombre de la pagina que deseas modificar. Te recuerdo que tus paginas son: \n"
            pags = DBManager.get_user_pages(DBManager.get_instance(), tracker.sender_id)
            for pag in pags:
                message += str(pag.name) + "\n"
            dispatcher.utter_message(text=message)
            message = "\n Además necesito que me proporciones el componente que quieras editar. Ellos pueden ser: \n"
            message += "Encabezado \n"
            message += "Footer \n"
            dispatcher.utter_message(text=message)
            return [SlotSet("pregunta_edicion", True)]


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
        PageManager.go_to_main_dir()
        ReactGenerator.generarHeader(dataHeader)
        print("-------------ENCABEZADO MODIFICADO-------------")
        DBManager.updt_modification_date(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'))
        dispatcher.utter_message(text="Podes ver los cambios que realizamos en el encabezado")
        return [SlotSet("creando_encabezado", False), SlotSet("componente", None)]


class ActionPreguntarMailFooter(Action):
    def name(self) -> Text:
        return "action_preguntar_mail_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTAR MAIL FOOTER----")
        dispatcher.utter_message(text="Queres cambiar tu e-mail en el footer?")
        return [SlotSet("creando_footer", True), FollowupAction("action_listen")]

class ActionGuardarMailFooter(Action):
    def name(self) -> Text:
        return "action_guardar_mail_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION GUARDAR MAIL FOOTER----")
        last_message_intent = tracker.latest_message.get('intent').get('name')
        print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
        if 'decir_mail' in last_message_intent:
        #El usuario proporciono el mail
            mail = tracker.get_slot('mail')
            print("(" + threading.current_thread().getName() + ") " + "------------mail: ", mail)
            #Guardar el mail en la pagina
            DBManager.set_page_mail(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), mail)
            dispatcher.utter_message(text="E-mail guardado.")
            return [SlotSet("mail_footer", mail), FollowupAction("utter_preguntar_ubicacion")]
        elif 'denegar' in last_message_intent:
        #El usuario no quiere modificar el mail
            print("(" + threading.current_thread().getName() + ") " + "------------denegar")
            dispatcher.utter_message(text="Perfecto, no se modificara el mail mostrado en el footer de su pagina.")
            return []
        else:
            print("(" + threading.current_thread().getName() + ") " + "------------default fallback")
            return [FollowupAction("action_default_fallback")]

class ActionGuardarUbicacionFooter(Action):
    def name(self) -> Text:
        return "action_guardar_ubicacion_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION GUARDAR UBICACION FOOTER----")
        last_message_intent = tracker.latest_message.get('intent').get('name')
        print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
        if 'decir_ubicacion' in last_message_intent:
        #El usuario proporciono su ubicacion
            ubicacion = tracker.get_slot("ubicacion")
            print("(" + threading.current_thread().getName() + ") " + "------------ubicacion: ", ubicacion)
            #Guardar la ubicacion en la pagina
            DBManager.set_page_location(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), ubicacion)
            dispatcher.utter_message(text="Ubicacion guardada.")
            return [SlotSet("ubicacion_footer", ubicacion), FollowupAction("action_crear_footer")]
        elif 'denegar' in last_message_intent:
        #El usuario no quiere modificar el mail
            print("(" + threading.current_thread().getName() + ") " + "------------denegar")
            dispatcher.utter_message(text="Perfecto, no se modificara la ubicacion mostrada en el footer de su pagina.")
            return [FollowupAction("action_crear_footer")]
        else:
            print("(" + threading.current_thread().getName() + ") " + "------------default fallback")
            return [FollowupAction("action_default_fallback")]

class ActionCrearFooter(Action):
    def name(self) -> Text:
        return "action_crear_footer"

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
        return [SlotSet("creando_encabezado", False), SlotSet("componente", None)]



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
        return [FollowupAction("action_restart")]


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
