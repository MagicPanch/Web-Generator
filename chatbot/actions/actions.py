import re
import threading
import datetime
import pandas as pd
from io import BytesIO
from numpy import nan

from resources import CONSTANTS, utils
from database.DBManager import DBManager
from generator.PageManager import PageManager
from generator.ReactGenerator import ReactGenerator
from generator.TelegramBotManager import TelegramBotManager
from generator.objects.pages.Front import Front
from generator.objects.sections.EcommerceSection import EcommerceSection
from generator.objects.sections.InformativeSection import InformativeSection

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction

slots_crear_pagina = ['creando_pagina', 'pregunta_nombre']
slots_crear_seccion = ['creando_seccion']
creando_pagina = False
dbm = DBManager()
pgm = PageManager()
rg = ReactGenerator()
tbm = TelegramBotManager()

#Actions Pagina
class ActionCapturarCreacion(Action):

    def name(self) -> Text:
        return "action_capturar_creacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR CREACION----")
        user_id = tracker.sender_id
        tuto = dbm.get_user_tutorial(user_id)
        if tuto:
            seccion = tracker.get_slot('componente')
            if seccion:
                pages = dbm.get_user_pages(user_id)
                if len(pages) > 0:
                    return [FollowupAction("action_capturar_tipo_seccion"), SlotSet("creando_seccion", True)]
                else:
                    dispatcher.utter_message(text="Antes de crear secciones debes crear una página")
            else:
                return [FollowupAction("action_preguntar_nombre_pagina"), SlotSet("creando_pagina", True)]
        else:
            dispatcher.utter_message(text="Para crear una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

class ActionPreguntarNombrePagina(Action):

    def name(self):
        return "action_preguntar_nombre_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTAR NOMBRE PAGINA----")
        tuto = dbm.get_user_tutorial(tracker.sender_id)
        if tuto:
            dispatcher.utter_message(text="¿Como queres que se llame tu pagina? Por favor indica su nombre en el siguiente formato: www. nombre-pagina .com")
            return [SlotSet("creando_pagina", True), SlotSet("pregunta_nombre", True)]
        else:
            dispatcher.utter_message(text="Para crear una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global creando_pagina, dbm, pgm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR PAGINA----")
        print("(" + threading.current_thread().getName() + ") " + "--------page_name_slot: ", tracker.get_slot('page_name'))
        print("creando_pagina: ", creando_pagina)
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')
        last_message_intent = tracker.latest_message.get('intent').get('name')
        if not 'nombre_pagina' in last_message_intent:
            dispatcher.utter_message(text="Entendido, si mas tarde deseas retomar la creacion de tu pagina puedes pedirmelo.")
            return [SlotSet("creando_pagina", False), SlotSet("pregunta_nombre", False)]

        if tracker.get_slot("creando_pagina"):
            if not page_name:
                dispatcher.utter_message(
                    text="Repetime como queres que se llame tu página. Te recuerdo que el formato es: www. nombre-pagina .com")
                return [SlotSet("creando_pagina", True), SlotSet("pregunta_nombre", True)]
            else:
                if creando_pagina:
                    page = pgm.get_page(user_id, page_name)
                    message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page.get_page_address()
                    dispatcher.utter_message(text=message)
                    message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
                    dispatcher.utter_message(text=message)
                    creando_pagina = False
                    events = []
                    for slot in slots_crear_pagina:
                        events.append(SlotSet(slot, False))
                    return events
                elif dbm.get_page_by_name(page_name) is None:
                    #La pagina no existe

                    #Se guarda su entrada en la base de datos
                    dbm.add_page(user_id, page_name, tracker.get_slot('usuario'))

                    #Se crea la entrada para la pagina en PageManager
                    pgm.add_page(user_id, page_name, True)

                    #Se crea en un nuevo hilo el proyecto de la pagina
                    pgm.create_project(user_id, page_name)
                    creando_pagina = True

                    dispatcher.utter_message(text="Aguarda un momento mientras se crea tu página. Este proceso puede demorar unos minutos.")
                    return [SlotSet("creando_pagina", False), FollowupAction("action_ejecutar_dev")]
                else:
                    #La pagina ya existe
                    dispatcher.utter_message(text="Ya existe una pagina con ese nombre. Por favor elige otro.")
                    return [SlotSet("creando_pagina", False), SlotSet("pregunta_nombre", True)]
        else:
            return []
class ActionEjecutarDev(Action):

    def name(self) -> Text:
        return "action_ejecutar_dev"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global creando_pagina, pgm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR DEV----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')

        #Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
        pgm.run_dev(user_id, page_name)

        page = pgm.get_page(user_id, page_name)
        message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page.get_page_address()
        dispatcher.utter_message(text=message)

        message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
        dispatcher.utter_message(text=message)
        events = []
        for slot in slots_crear_pagina:
            events.append(SlotSet(slot, False))
        return events

class ActionEjecutarPagina(Action):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR PAGINA----")
        user_id = tracker.sender_id
        tuto = dbm.get_user_tutorial(user_id)
        if tuto:
            page_name = tracker.get_slot('page_name')
            if page_name is None:
                message = "Indicame el nombre de la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
                pags = dbm.get_user_pages(tracker.sender_id)
                for pag in pags:
                    message += str(pag['name']) + "\n"
                return [SlotSet("pregunta_ejecucion", True)]
            else:
                # Se estuvo hablando de una pagina en particular
                page_doc = dbm.get_page(user_id, page_name)
                print("(" + threading.current_thread().getName() + ") " + "--------page_doc: ", page_doc)
                if not page_doc:
                    # Esa pagina no pertenece al usuario
                    message = "No se encuentra la pagina que deseas ejecutar. Te recuerdo que tus paginas son:\n"
                    pags = dbm.get_user_pages(user_id)
                    for pag in pags:
                        message += str(pag['name']) + "\n"
                    dispatcher.utter_message(text=message)
                    return [SlotSet("pregunta_ejecucion", True)]
                else:
                # La pagina pertenece al usuario
                    if pgm.is_alive(user_id, page_name):
                    # La pagina esta viva
                        page_obj = pgm.get_page(user_id, page_name)
                        if page_obj.is_running():
                        # Verificar si la pagina está ejecutando
                            dispatcher.utter_message(text="Tu pagina ya esta ejecutando. Puedes acceder a ella en el siguiente link: " + page_obj.get_page_address())
                            dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
                            return []
                        elif page_obj.is_running_dev():
                        # Se esta ejecutando en modo dev
                            pgm.stop_page(user_id, page_name)
                            pgm.stop_tunnel(user_id, page_name)
                    else:
                    # La pagina no vive en PageManager
                        page_obj = pgm.add_page(user_id, page_name)
                    #Verificar si esta compilada
                    if not dbm.was_compiled(user_id, page_name):
                        print("(" + threading.current_thread().getName() + ") " + "----------------pagina no compilada")
                        pgm.build_project(user_id, page_name)
                        dbm.set_compilation_date(user_id, page_name)
                        pgm.join_thread_exec(user_id, page_name)
                        print("(" + threading.current_thread().getName() + ") " + "------------PAGINA COMPILADA")
                    else:
                        print("(" + threading.current_thread().getName() + ") " + "----------------pagina ya compilada")

                    # Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
                    pgm.run_project(user_id, page_name)

                    page_address = page_obj.get_page_address()
                    print("(" + threading.current_thread().getName() + ") " + "------------page_address: ", page_address)
                    dispatcher.utter_message(text="Podes acceder a tu página en el siguiente link: " + page_address)
                    dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
                    return [SlotSet("pregunta_ejecucion", False)]
        else:
            dispatcher.utter_message(text="Para ejecutar una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

    class ActionDetenerPagina(Action):

        def name(self) -> Text:
            return "action_detener_pagina"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            global dbm, pgm
            print("(" + threading.current_thread().getName() + ") " + "----ACTION DETENER PAGINA----")
            last_message_entities = tracker.get_latest_entity_values("text")
            print("(" + threading.current_thread().getName() + ") " + "--------last_message_entities: ", last_message_entities)
            user_id = tracker.sender_id
            tuto = dbm.get_user_tutorial(user_id)
            if tuto:
                if "todas" in tracker.latest_message.get("text"):
                # Quiere detener todas
                    for pag in pgm.get_user_running_pages(user_id):
                        pgm.stop_page(user_id, pag.get_name())
                        pgm.stop_tunnel(user_id, pag.get_name())
                        pgmpgm.pop_page(user_id, pag.get_name())
                        dispatcher.utter_message(text="La pagina " + pag.get_name() + " fue detenida con éxito.")
                    print("(" + threading.current_thread().getName() + ") " + "------------PAGINAS DETENIDA CON EXITO------------")
                else:
                #No especifico cual quiere detener pero hay slot de contexto
                    page_name = tracker.get_slot('page_name')
                    if page_name:
                        pgm.stop_page(user_id, page_name)
                        pgm.stop_tunnel(user_id, page_name)
                        pgm.pop_page(user_id, page_name)
                        print("(" + threading.current_thread().getName() + ") " + "------------PAGINA DETENIDA CON EXITO------------")
                        dispatcher.utter_message(text="Tu pagina fue apagada con exito.")
                    else:
                        message = "Indicame el nombre de la pagina que deseas detener. Te recuerdo que tus paginas en ejecución son: \n"
                        pags = pgm.get_user_running_pages(user_id)
                        for pag in pags:
                            message += str(pag.get_name()) + "\n"
                        dispatcher.utter_message(message)
                        return [SlotSet("pregunta_detencion", True)]
                return [SlotSet("pregunta_detencion", False)]
            else:
                dispatcher.utter_message(text="Para detener una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
                return [SlotSet("pregunta_tutorial", True)]

class ActionCapturarEdicion(Action):

    def name(self) -> Text:
        return "action_capturar_edicion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR EDICION----")
        user_id = tracker.sender_id
        tuto = dbm.get_user_tutorial(user_id)
        if tuto:
            pages = dbm.get_user_pages(user_id)
            if len(pages) > 0:
                page_name = tracker.get_slot('page_name')
                print("(" + threading.current_thread().getName() + ") " + "--------pagina: ", page_name)
                if page_name:
                # Hay pagina
                    page_doc = dbm.get_page(user_id, page_name)
                    print("(" + threading.current_thread().getName() + ") " + "--------page_doc: ", page_doc)
                    if not page_doc:
                    # Esa pagina no pertenece al usuario
                        message = "La pagina que estas intentando modificar no te pertenece. Te recuerdo que tus paginas son: "
                        pags = dbm.get_user_pages(user_id)
                        for pag in pags:
                            message += str(pag.name) + "\n"
                        dispatcher.utter_message(text=message)
                        return [SlotSet("pregunta_nombre", True)]
                    else:
                    # La pagina es del usuario
                        if pgm.is_alive(user_id, page_name):
                        # La pagina esta viva
                            page_obj = pgm.get_page(user_id, page_name)
                            if page_obj.is_running():
                                pgm.switch_dev(user_id, page_name)
                            dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address())
                            dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
                            if not page_obj.is_running_dev():
                                pgm.run_dev(user_id, page_name)
                                dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address())
                                dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
                        else:
                        # La pagina no está viva, hay que recuperar sus datos de la db
                            page_obj = pgm.add_page(user_id, page_name)
                            pgm.run_dev(user_id, page_name)
                    componente = tracker.get_slot('componente')
                    print("(" + threading.current_thread().getName() + ") " + "--------componente: ", componente)
                    if componente:
                    # Hay componente a modificar
                        if componente.lower() == "encabezado":
                            return [FollowupAction("action_preguntar_color_encabezado"), SlotSet("pregunta_componente", False),
                                    SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                        elif componente.lower() == "footer":
                            return [FollowupAction("action_preguntar_mail_footer"), SlotSet("pregunta_componente", False),
                                    SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                        elif componente.lower() == "seccion":
                        # Va a editar una seccion
                            tipo_seccion = tracker.get_slot('tipo_seccion')
                            print("(" + threading.current_thread().getName() + ") " + "--------tipo_seccion: ", tipo_seccion)
                            nombre_seccion = tracker.get_slot('nombre_informativa')
                            print("(" + threading.current_thread().getName() + ") " + "--------nombre_informativa: ", nombre_seccion)
                            secciones = page_obj.get_sections_name()
                            if len(secciones) > 0:
                            # La pagina tiene secciones
                                if nombre_seccion:
                                    if nombre_seccion.lower() == "e-commerce":
                                        message = "No hay modificaciones que puedas realizar en la sección e-commerce de tu página. Si queres agregar productos debes pedirmelo como tal."
                                        dispatcher.utter_message(text=message)
                                        return [SlotSet("componente", None), SlotSet("tipo_seccion", None), SlotSet("nombre_informativa", None), SlotSet("pregunta_edicion", False)]
                                    if nombre_seccion in secciones:
                                        return [SlotSet("nombre_seccion_editando", nombre_seccion), FollowupAction("action_modificar_informativa_1"), SlotSet("pregunta_componente", False),  SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                                    else:
                                        dispatcher.utter_message(text=str(nombre_seccion) + " no es un tipo de seccion válido. Te recuerdo que las secciones a crear son: \n E-Commerce \n Informativa")
                                        return [SlotSet("pregunta_componente", True), SlotSet("pregunta_seccion", True)]
                                else:
                                    message = str(tipo_seccion) + " no es un tipo de seccion válido. Te recuerdo que las secciones de tu página son:\n"
                                    for seccion in secciones:
                                        message += seccion + "\n"
                                    dispatcher.utter_message(text=message)
                                    return [SlotSet("pregunta_componente", True), SlotSet("pregunta_seccion", True)]
                            else:
                            # La pagina no tiene secciones
                                dispatcher.utter_message(text="La pagina " + page_doc.name + " no cuenta con ninguna sección, por lo que antes deberás crear una.")
                                return [FollowupAction("action_capturar_tipo_seccion")]
                    else:
                    # No hay componente a modificar
                        message = "¿Qué componente de tu página te gustaría modificar? Te recuerdo que sus componentes son:\nEncabezado\n"
                        secciones = page_obj.get_sections_name()
                        if len(secciones) > 0:
                            for seccion in secciones:
                                message += "Seccion " + seccion + "\n"
                        message += "Footer"
                        dispatcher.utter_message(text=message)
                        return [SlotSet("pregunta_componente", True)]
                else:
                # No hay página
                    if len(pages) > 0:
                        message = "¿Qué página te gustaría modificar? Te recuerdo que tus páginas son:\n"
                        for page in pages:
                            message += str(page.name) + "\n"
                    else:
                        message = "Antes de realizar modificaciones debes crear una página"
                    dispatcher.utter_message(text=message)
                    return [SlotSet("pregunta_nombre", True)]
            else:
            # Tiene páginas
                dispatcher.utter_message(text="Antes de realizar modificaciones debes crear una página")
        else:
            dispatcher.utter_message(text="Para modificar una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]


class ActionGuardarColor(Action):
    def name(self) -> Text:
        return "action_guardar_color"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----EN ACTION GUARDAR COLOR----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        color = next(tracker.get_latest_entity_values("color"), None)
        print("(" + threading.current_thread().getName() + ") " + "--------color: ", color)
        #text - yellow - 600
        if not color or tracker.get_intent_of_latest_message() == "despues_te_digo":
            message = "Bien, mantendremos el color actual"
        else:
            message = "Color capturado."
        dispatcher.utter_message(text=str(message))
        slot_key = None
        if tracker.get_slot("creando_encabezado"):
            slot_key = "color_encabezado"
        if slot_key is not None:
            print("(" + threading.current_thread().getName() + ") " + "--------slot_key: ", slot_key)
            return [SlotSet(slot_key, color)]
        else:
            return []


class ActionRecibirImagen(Action):
    def name(self) -> Text:
        return "action_recibir_imagen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm, tbm
        print("(" + threading.current_thread().getName() + ") " + "----EN ACTION RECIBIR IMAGEN----")
        print("(" + threading.current_thread().getName() + ") " + "--------creando_encabezado ", tracker.get_slot("creando_encabezado"))
        print("(" + threading.current_thread().getName() + ") " + "--------creando_seccion_informativa ", tracker.get_slot("creando_seccion_informativa"))
        print("(" + threading.current_thread().getName() + ") " + "--------pregunta_otra_imagen_seccion_informativa ", tracker.get_slot("pregunta_otra_imagen_seccion_informativa"))
        print("(" + threading.current_thread().getName() + ") " + "--------last_message_intent: ", tracker.latest_message.get('intent').get('name'))

        # Verifica si el último mensaje contiene una imagen
        latest_message = tracker.latest_message
        if 'photo' in latest_message['metadata']['message']:
            error = False
            photo = latest_message['metadata']['message']['photo'][1]
            image_id = photo['file_id']
            page_path = pgm.get_page_path(tracker.sender_id, tracker.get_slot("page_name"))
            if not image_id:
                error = True
            else:
                if tracker.get_slot("creando_encabezado"):
                    utils.go_to_main_dir()
                    tbm.download_image(page_path=page_path, subdir="components", image_id=image_id, image_name="logo.png")
                elif tracker.get_slot("creando_seccion_informativa"):
                    utils.go_to_main_dir()
                    tbm.download_image(page_path=page_path, subdir="sect_inf_images", image_id=image_id, image_name=(photo["file_unique_id"] + ".png"))
                elif tracker.get_slot("agregando_productos"):
                    #Descargar imagen
                    image_url = telegram_bot.get_image_url(image_id=image_id)
                    dbm.set_product_multimedia(tracker.sender_id, tracker.get_slot("page_name"), tracker.get_slot("id_producto"), image_url)
            if not error:
                dispatcher.utter_message(text="Imagen recibida con éxito.")
                if tracker.get_slot("creando_encabezado"):
                    return [FollowupAction("action_crear_encabezado")]
                elif tracker.get_slot("creando_seccion_informativa"):
                    dispatcher.utter_message(text="¿Queres agregar otra imagen?")
                    return [SlotSet("pregunta_otra_imagen_seccion_informativa", True)]
                elif tracker.get_slot("agregando_productos"):
                    dispatcher.utter_message(text="¿Queres cargar otro producto?")
                    return [SlotSet("pregunta_carga", True), SlotSet("pide_img_prod", False)]
            else:
                dispatcher.utter_message(text="No se pudo procesar la imagen.")
        else:
            if tracker.latest_message.get('intent').get('name') == "denegar":
                if tracker.get_slot("creando_encabezado"):
                    dispatcher.utter_message(text="Perfecto, el encabezado de tu página no contendrá ningún logo")
                    return [FollowupAction("action_crear_encabezado")]
                elif tracker.get_slot("creando_seccion_informativa"):
                    return [SlotSet("pregunta_otra_imagen_seccion_informativa", False)]
                elif tracker.get_slot("editando_seccion_informativa"):
                    return [SlotSet("pregunta_otra_imagen_seccion_informativa", False)]
                elif tracker.get_slot("agregando_productos"):
                    return [SlotSet("agregando_productos", False), SlotSet("pregunta_carga", False)]
        return []

class ActionPreguntarColorEncabezado(Action):
    def name(self) -> Text:
        return "action_preguntar_color_encabezado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="De que color te gustaria que sea el encabezado? Para ello necesito que me proveas su codigo hexadecimal. Podes seleccionar tu color y copiar su codigo en el siguiente link: https://g.co/kgs/FMBcG8K")
        return [SlotSet("creando_encabezado", True), SlotSet("pregunta_color", True), FollowupAction("action_listen")]


class ActionCrearEncabezado(Action):
    def name(self) -> Text:
        return "action_crear_encabezado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm, rg
        print("(" + threading.current_thread().getName() + ")" + "----EN ACTION CREAR ENCABEZADO----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        page_path = pgm.get_page_path(tracker.sender_id, tracker.get_slot('page_name'))
        print("(" + threading.current_thread().getName() + ")" + "--------page_path: ", page_path)
        color = tracker.get_slot('color_encabezado')
        print("(" + threading.current_thread().getName() + ")" + "--------color: ", color)
        dataHeader = {
            "titulo": tracker.get_slot('page_name'),
            "address": page_path,
            "addressLogo": "./logo.png",
            "colorTitulo": color
        }
        utils.go_to_main_dir()
        rg.generarHeader(dataHeader)
        print("-------------ENCABEZADO MODIFICADO-------------")
        dbm.updt_modification_date(tracker.sender_id, tracker.get_slot('page_name'))
        dispatcher.utter_message(text="Podes ver los cambios que realizamos en el encabezado")
        return [SlotSet("creando_encabezado", False), SlotSet("componente", None)]


class ActionPreguntarMailFooter(Action):
    def name(self) -> Text:
        return "action_preguntar_mail_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTAR MAIL FOOTER----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        dispatcher.utter_message(text="Queres cambiar tu e-mail en el footer?")
        return [SlotSet("creando_footer", True), FollowupAction("action_listen")]

class ActionGuardarMailFooter(Action):
    def name(self) -> Text:
        return "action_guardar_mail_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION GUARDAR MAIL FOOTER----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        last_message_intent = tracker.latest_message.get('intent').get('name')
        print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
        if 'decir_mail' in last_message_intent:
        #El usuario proporciono el mail
            mail = tracker.get_slot('mail')
            print("(" + threading.current_thread().getName() + ") " + "------------mail: ", mail)
            #Guardar el mail en la pagina
            dbm.set_page_mail(tracker.sender_id, tracker.get_slot('page_name'), mail)
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
        global dbm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION GUARDAR UBICACION FOOTER----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        last_message_intent = tracker.latest_message.get('intent').get('name')
        print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
        if 'decir_ubicacion' in last_message_intent:
        #El usuario proporciono su ubicacion
            ubicacion = tracker.get_slot("ubicacion")
            print("(" + threading.current_thread().getName() + ") " + "------------ubicacion: ", ubicacion)
            #Guardar la ubicacion en la pagina
            dbm.set_page_location(tracker.sender_id, tracker.get_slot('page_name'), ubicacion)
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
        global pgm, rg
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR FOOTER----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        page_path = pgm.get_page_path(tracker.sender_id, tracker.get_slot('page_name'))
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
        utils.go_to_main_dir()
        rg.generarFooter(dataFooter)
        print("-------------FOOTER MODIFICADO-------------")
        dispatcher.utter_message(text="Podes ver los cambios que realizamos en el footer")
        return [SlotSet("creando_footer", False), SlotSet("componente", None)]

# SECCIONES

## CREAR
class ActionCapturarTipoSeccion(Action):
    def name(self) -> Text:
        return "action_capturar_tipo_seccion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR TIPO SECCION----")
        page_name = tracker.get_slot("page_name")
        print("(" + threading.current_thread().getName() + ") " + "--------page_name: ", page_name)
        if page_name:
            page_doc = dbm.get_page(tracker.sender_id, page_name)
            if not page_doc:
                print("(" + threading.current_thread().getName() + ") " + "--------page_doc: ", page_doc)
                # Esa pagina no pertenece al usuario
                message = "No se encuentra la pagina a la que deseas crearle una sección. Te recuerdo que tus paginas son: \n"
                pags = dbm.get_user_pages(tracker.sender_id)
                for pag in pags:
                    message += pag.name + "\n"
                dispatcher.utter_message(text=message)
                return [SlotSet("pregunta_nombre", True), SlotSet("componente", "seccion")]
            else:
                print("(" + threading.current_thread().getName() + ") " + "--------page_doc.name: ", page_doc.name)
                page_obj = pgm.get_page(tracker.sender_id, page_doc.name)
                if not page_obj:
                    page_obj = pgm.add_page(tracker.sender_id, page_doc.name)
                print("(" + threading.current_thread().getName() + ") " + "--------page_obj.name: ", page_obj.get_name())
                if not tracker.get_slot('tipo_seccion') == "e-commerce":
                    if not page_obj.is_running_dev():
                        pgm.run_dev(tracker.sender_id, page_doc.name)
                        page_obj.wait_for_ready()
                        message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address()
                        dispatcher.utter_message(text=message)
                        message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
                        dispatcher.utter_message(text=message)
                    elif page_obj.is_running():
                        pgm.switch_dev(tracker.sender_id, page_doc.name)
                        message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address()
                        dispatcher.utter_message(text=message)
                        message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
                        dispatcher.utter_message(text=message)
            seccion = tracker.get_slot('componente')
            if seccion.lower() == "seccion":
            # Va a editar una seccion
                tipo_seccion = tracker.get_slot('tipo_seccion')
                print("(" + threading.current_thread().getName() + ") " + "--------tipo_seccion: ", tipo_seccion)
                if tipo_seccion:
                    # Hay tipo seccion
                    if "e-commerce" in tipo_seccion.lower():
                        dispatcher.utter_message(text="Aguarda un momento mientras se crea la sección e-commerce en tu página.")
                        return [FollowupAction("action_crear_ecommerce")]
                    elif "informativa" in tipo_seccion.lower():
                        return [FollowupAction("action_crear_informativa_1"), SlotSet("pregunta_edicion", False)]
                    else:
                        dispatcher.utter_message(text=str(tipo_seccion) + " no es un tipo de seccion válido. Te recuerdo que las secciones a crear son: \n E-Commerce \n Informativa")
                        return [SlotSet("pregunta_seccion", True), SlotSet("pregunta_nombre", True), SlotSet("componente", "seccion")]
                else:
                    # No hay tipo seccion
                    dispatcher.utter_message(text="¿Que tipo de sección te gustaría crear? Te recuerdo que las posibles secciones son: \n E-Commerce \n Informativa")
                    return [SlotSet("pregunta_seccion", True), SlotSet("pregunta_nombre", True)]
            return [SlotSet("creando_seccion", True), SlotSet("pregunta_nombre", True), SlotSet("componente", "seccion")]
        else:
            message = "Indicame el nombre de la pagina en la que deseas crear la sección. Te recuerdo que tus paginas son: \n"
            pags = dbm.get_user_pages(tracker.sender_id)
            for pag in pags:
                message += str(pag.name) + "\n"
            dispatcher.utter_message(text=message)
            return [SlotSet("pregunta_nombre", True), SlotSet("componente", "seccion")]

### E-COMMERCE

class ActionCrearEcommerce(Action):

    def name(self):
        return "action_crear_ecommerce"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION E-COMMERCE----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot("page_name")
        page = pgm.get_page(user_id, page_name)
        seccion = page.get_section("e-commerce")
        if seccion:
            dispatcher.utter_message(text="Tu página ya tiene una sección de e-commerce.")
        else:
            page.add_section(EcommerceSection())
            pgm.add_ecommerce(user_id, page_name)
            if not page.is_running_dev():
                pgm.run_dev(user_id, page_name)
                message = "Tu pagina se encuentra en modo edición. Podrás visualizar la nueva sección en: " + page.get_page_address()
                dispatcher.utter_message(text=message)
                message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Podes ver la nueva sección en tu página.")
            dbm.add_ecomm_section(user_id, page_name)
        return [SlotSet("pregunta_seccion", False), SlotSet("creando_seccion", False), SlotSet("componente", None)]

#### AGREGAR PRODUCTOS

class ActionPedirProductos(Action):

    def name(self) -> Text:
        return "action_pedir_productos"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, tbm
        user_id = tracker.sender_id
        page_name = tracker.get_slot("page_name")
        tuto = dbm.get_user_tutorial(user_id)
        if tuto:
            pages = dbm.get_user_pages(user_id)
            if len(pages) > 0:
                if page_name:
                # Hay página
                    page_doc = dbm.get_page(user_id, page_name)
                    if page_doc:
                    # Es del usuario
                        if page_doc.has_ecomm_section:
                        # Tiene sección ecommerce
                            print("(" + threading.current_thread().getName() + ") " + "----ACTION PEDIR PRODUCTOS----")
                            message = "Podes agregar los productos de a uno o cargar múltiples productos en un archivo de datos y enviármelo. Si optas por la carga mediante archivo, completa la siguiente planilla agregando los datos en una nueva fila. En los campos \"multimedia\" coloca el link a las imágenes o videos del producto"
                            dispatcher.utter_message(text=message)
                            utils.go_to_main_dir()
                            tbm.send_file_to_user(user_id, CONSTANTS.TEMPLATE_PRODUCTOS_DIR)
                            dispatcher.utter_message(text="Si vas a cargar los productos de a uno voy a necesitar los siguientes datos:")
                            dispatcher.utter_message(text="Cantidad:\nTitulo:\nDescripción:\nPrecio:")
                            return [SlotSet("agregando_productos", True), SlotSet("pregunta_carga", True), SlotSet("pregunta_nombre", False)]
                        else:
                        # No tiene sección ecommerce
                            message = "La página " + str(page_name) + " no tiene sección e-commerce."
                            pages = dbm.get_user_pages(user_id, "e-commerce")
                            if len(pages) > 0:
                                message += " Tus páginas con dicha sección son:\n"
                                for page in pages:
                                    if page.has_ecomm_section:
                                        message += str(page.name) + "\n"
                            dispatcher.utter_message(text=message)
                            return [SlotSet("agregando_productos", True), SlotSet("pregunta_nombre", True)]
                    else:
                    # No es del usuario
                        message = "La página " + str(page_name) + " no te pertenece."
                        if len(pages) > 0:
                            message += " Te recuerdo que tus páginas con sección e-commerce son:\n"
                            for page in pages:
                                if page.has_ecomm_section:
                                    message += str(page.name) + "\n"
                        dispatcher.utter_message(text=message)
                        return [SlotSet("agregando_productos", True), SlotSet("pregunta_nombre", True)]
                else:
                # No hay página
                    pages = dbm.get_user_pages(user_id, "e-commerce")
                    if len(pages) > 0:
                        message = "¿A qué página te gustaría agregar productos? Te recuerdo que tus páginas con sección e-commerce son:\n"
                        for page in pages:
                            if page.has_ecomm_section:
                                message += str(page.name) + "\n"
                    else:
                        message = "No tienes ninguna página con una sección e-commerce."
                    dispatcher.utter_message(text=message)
                    return [SlotSet("agregando_productos", True), SlotSet("pregunta_nombre", True)]
            else:
                dispatcher.utter_message(text="Para cargar productos primero debes crear una página")
        else:
            dispatcher.utter_message(text="Para cargar productos primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

class ActionCapturarProductoCargado(Action):

    def name(self) -> Text:
        return "action_capturar_producto_cargado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, tbm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR PRODUCTO CARGADO----")
        # Verifica si el último mensaje contiene una imagen
        latest_message = tracker.latest_message
        if 'document' in latest_message['metadata']['message']:
            error = False
            documento = latest_message['metadata']['message']['document']
            file_id = documento['file_id']
            if not documento:
                error = True
            else:
                file = tbm.get_csv_file(file_id)
                file_bytes = BytesIO()
                file.download(out=file_bytes)
                file_bytes.seek(0)
                df = pd.read_excel(file_bytes, engine='openpyxl')
                for producto in df.itertuples(index=True, name='Pandas'):
                    id = dbm.add_product(user_id=tracker.sender_id, page_name=tracker.get_slot("page_name"), cant=producto.Cantidad, title=producto.Titulo, desc=producto.Descripcion, precio=float(producto.Precio))
                    if producto.Imagen_principal is not nan:
                        dbm.set_product_multimedia(tracker.sender_id, tracker.get_slot("page_name"), id, str(producto.Imagen_principal))
                    message = "El producto " + producto.Titulo + " se guardó correctamente con el identificador: " + str(id)
                    dispatcher.utter_message(text=message)
                dispatcher.utter_message(text="Ha finalizado la carga de productos. ¿Puedo ayudarte con algo más?")
                return [SlotSet("agregando_productos", False), SlotSet("pregunta_carga", False)]
            if error:
                dispatcher.utter_message(text="No se pudo recibir el archivo. Por favor envíalo nuevamente.")
                return [SlotSet("agregando_productos", True), SlotSet("pregunta_carga", True)]
        else:
            last_message = str(tracker.latest_message.get('text'))
            print("(" + threading.current_thread().getName() + ") " + "--------last_message: \n", last_message)
            cant = tracker.get_slot("cant_prod")
            print("(" + threading.current_thread().getName() + ") " + "--------cant: \n", cant)
            titulo = tracker.get_slot("tit_prod")
            if not titulo:
                patron_titulo = r"Titulo: (.+?)\nDescripción:"
                titulo = re.search(patron_titulo, last_message, re.DOTALL).group(1)
            print("(" + threading.current_thread().getName() + ") " + "--------titulo: \n", titulo)
            desc = tracker.get_slot("desc_prod")
            if not desc:
                patron_descripcion = r"Descripción: (.+?)\nPrecio:"
                desc = re.search(patron_descripcion, last_message, re.DOTALL).group(1)
            print("(" + threading.current_thread().getName() + ") " + "--------desc: \n", desc)
            precio = tracker.get_slot("precio_prod")
            if precio:
                precio = precio.replace(",", ".")
            print("(" + threading.current_thread().getName() + ") " + "--------precio: \n", precio)
            id = dbm.add_product(user_id=tracker.sender_id, page_name=tracker.get_slot("page_name"), cant=cant, title=titulo, desc=desc, precio=float(precio))
            message = "El producto " + titulo + " se guardó correctamente con el identificador: " + str(id)
            dispatcher.utter_message(text=message)
            dispatcher.utter_message(text="Si lo deseas podes enviarme alguna imagen sobre él.")
            return [SlotSet("pide_img_prod", True), SlotSet("id_producto", id)]


### INFORMATIVA

class ActionCrearInformativa1(Action):

    def name(self) -> Text:
        return "action_crear_informativa_1"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 1----")
        dispatcher.utter_message(text="¿Que nombre llevará la sección?")
        return [SlotSet("creando_seccion_informativa", True), SlotSet("pregunta_nombre_informativa", True)]


class ActionCrearInformativa2(Action):

    def name(self) -> Text:
        return "action_crear_informativa_2"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global pgm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 2----")
        print("(" + threading.current_thread().getName() + ") " + "--------page_name: ", tracker.get_slot('page_name'))
        page = pgm.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        nombre_informativa = "Informacion"
        last_message_intent = tracker.latest_message.get('intent').get('name')
        if "decir_nombre_informativa" in last_message_intent:
            nombre_informativa = tracker.get_slot("nombre_informativa")
            dispatcher.utter_message(text="Nombre de sección guardado.")
        inf_section = InformativeSection(nombre_informativa)
        page.add_section(inf_section)
        dispatcher.utter_message(text="Proporcioname el texto informativo. Por favor, respeta el siguiente formato:")
        dispatcher.utter_message(text="###\nTexto\n###")
        return [SlotSet("creando_seccion_informativa", True), SlotSet("pide_text_informativa", True), SlotSet("pregunta_nombre_informativa", False)]


class ActionCrearInformativa3(Action):

    def name(self) -> Text:
        return "action_crear_informativa_3"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm, rg
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 3----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')
        last_user_message = str(tracker.latest_message.get('text'))
        text = last_user_message[3:len(last_user_message) - 3].strip()
        if tracker.get_slot("nombre_informativa"):
            nombre_informativa = tracker.get_slot("nombre_informativa")
        else:
            nombre_informativa = "Informacion"
        page = pgm.get_page(user_id, page_name)
        inf_section = page.get_section(nombre_informativa)
        inf_section.set_text(text)
        dispatcher.utter_message(text="Texto informativo guardado.")
        dbm.add_inf_section(user_id, page_name, inf_section)
        utils.go_to_main_dir()
        rg.agregarSectionInformativa(nombre_informativa, pgm.get_page_path(user_id, page_name), inf_section.get_text())
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("creando_seccion_informativa", False), SlotSet("pide_text_informativa", False), SlotSet("pregunta_seccion", False),
                SlotSet("creando_seccion", False), SlotSet("componente", None)]

## EDITAR

### INFORMATIVA

class ActionModificarInformativa1(Action):

    def name(self) -> Text:
        return "action_modificar_informativa_1"


    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION MODIFICAR SECCION INFORMATIVA 1----")
        dispatcher.utter_message(text="¿Cuál es el nuevo contenido de la sección?")
        return [SlotSet("creando_seccion_informativa", True), SlotSet("pide_text_informativa", True)]


class ActionModificarInformativa2(Action):

    def name(self) -> Text:
        return "action_modificar_informativa_2"


    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm, rg
        print("(" + threading.current_thread().getName() + ") " + "----ACTION MODIFICAR SECCION INFORMATIVA 2----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')
        last_user_message = str(tracker.latest_message.get('text'))
        text = last_user_message[3:len(last_user_message) - 3].strip()
        page = pgm.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        nombre_informativa = tracker.get_slot("nombre_informativa")
        inf_section = page.get_section(nombre_informativa)
        inf_section.set_text(text)
        dispatcher.utter_message(text="Texto informativo guardado.")
        dbm.updt_inf_section(user_id, page_name, nombre_informativa, text)
        utils.go_to_main_dir()
        rg.modificarSectionInformativa(nombre_informativa, pgm.get_page_path(), text)
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("editando_seccion_informativa", False), SlotSet("pide_text_informativa", False)]


class ActionModificarInformativa4(Action):

    def name(self) -> Text:
        return "action_modificar_informativa_4"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION MODIFICAR SECCION INFORMATIVA 4----")
        page = pgm.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        if tracker.get_slot("nombre_informativa"):
            nombre_informativa = tracker.get_slot("nombre_informativa")
        else:
            nombre_informativa = tracker.get_slot("nombre_seccion_editando")
        inf_section = page.get_section(nombre_informativa)
        dbm.updt_inf_section(tracker.sender_id, tracker.get_slot("page_name"), tracker.get_slot("nombre_seccion_editando"),  inf_section)
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("editando_seccion_informativa", False)]

# Saludo Actions
class ActionSaludoTelegram(Action):

    def name(self) -> Text:
        return "action_saludo_telegram"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        dispatcher.utter_message(text="#### AVISO #### \nPor el momento me encuentro en desarrollo, por lo que si la conversación no fluye como se espera, envia un mensaje con el comando \"/restart\" para reiniciar mis slots de contexto.")
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
        user_doc = dbm.get_user(ide)
        if user_doc:
        #El usuario ya existe
            dispatcher.utter_message(text="Bienvenido nuevamente " + nombre + ", ¿como puedo ayudarte?")
            if not user_doc.hizo_tutorial:
            #No hizo el tutorial
                dispatcher.utter_message(text="¿Quisieras completar el tutorial en esta ocasión? Te recuerdo que debes finalizarlo antes de poder empezar a crear tus páginas.")
                return [SlotSet("pregunta_tutorial", True), SlotSet("usuario", user_name), SlotSet("nombre_usuario", nombre), SlotSet("horario", horario), SlotSet("id_user", ide)]
        else:
        #El usuario no existe
            message = "Hola " + nombre + ", como va tu " + horario + "? Soy el Chatbot WebGenerator, encargado de ayudarte a crear tu pagina web! Si queres preguntame y te explico un poco en que cosas puedo contribuir."
            dispatcher.utter_message(text="Hola " + nombre + ", ¿como va tu " + horario + "? Soy el chatbot WebGenerator, tu asistente para crear páginas web.")
            dispatcher.utter_message(text="¿Queres realizar el tutorial?")
            dbm.add_user(ide, tracker.get_slot("usuario"), nombre)
            return [SlotSet("pregunta_tutorial", True), SlotSet("usuario", user_name), SlotSet("nombre_usuario", nombre), SlotSet("horario", horario), SlotSet("id_user", ide)]

        return [SlotSet("pregunta_tutorial", False), SlotSet("usuario", user_name), SlotSet("nombre_usuario", nombre), SlotSet("horario", horario), SlotSet("id_user", ide)]


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

class ActionResponderPaginasPropias(Action):

    def name(self) -> Text:
        return "action_responder_paginas_propias"


    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        pages = dbm.get_user_pages(tracker.sender_id)
        if pages:
            message = "Tus paginas son: \n"
            for page in pages:
                message += page.name + "\n"
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text="Todavía no creaste ninguna página.")
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

# TUTORIAL

class ActionCapturarTutorial(Action):

    def name(self) -> Text:
        return "action_capturar_tutorial"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR TUTORIAL----")
        last_message_intent = tracker.latest_message.get('intent').get('name')
        if 'denegar' in last_message_intent:
            dispatcher.utter_message(text="No hay problema, solo ten en cuenta que necesitarás completar el tutorial antes de empezar a crear tus páginas")
            return []
        elif 'afirmar' in last_message_intent or 'pedir_tutorial' in last_message_intent:
            dispatcher.utter_message(text="Excelente, daremos inicio al tutorial")
            return [SlotSet("inicia_tutorial", True)]
        else:
            return [FollowupAction("action_default_fallback")]

class ActionPregunta1(Action):

    def name(self) -> Text:
        return "action_pregunta_1"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 1----")
        dispatcher.utter_message(text="Nuestras páginas se construyen mediante componentes. El primero de ellos es el encabezado, que se encuentra en la parte superior de la página web.")
        dispatcher.utter_message(text="Este encabezado se compone por el título de la página, el color del título y un logo.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_1_confirmacion", True)]


class ActionPregunta1Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_1_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 1 REPETIR----")
        url_imagen = "https://ibb.co/dmsX1jY"
        dispatcher.utter_message(image=url_imagen)
        dispatcher.utter_message(text="En la imagen que esta arriba es un ejemplo de como esta formado el encabezado")
        dispatcher.utter_message(text="Este encabezado se compone por el título de la página, el color del título y un logo.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_1_confirmacion", False), SlotSet("pregunta_1_repetir_confirmacion", True)]


class ActionPregunta2(Action):

    def name(self) -> Text:
        return "action_pregunta_2"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 2----")
        dispatcher.utter_message(text="El siguiente componente de nuestras páginas es el cuerpo, el cual dividimos según 3 tipos de secciones: e-commerce e informativa.")
        dispatcher.utter_message(text="Seccion e-commerce: \nEsta sección te permite montar una tienda en tu página, cargar productos y que los usuarios puedan comprarlos.")
        dispatcher.utter_message(text="Seccion informativa: \nEsta sección te permite incluir información sobre tu página o empresa, incluyendo un texto informativo e imágenes.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_2_confirmacion", True), SlotSet("pregunta_2_repetir_confirmacion", False)]


class ActionPregunta2Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_2_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 2 REPETIR----")
        url_imagen = "https://ibb.co/gTbpK4J"
        dispatcher.utter_message(text="Nuestras páginas cuentan con múltiples secciones.")
        dispatcher.utter_message(image=url_imagen)
        url_imagen = "https://ibb.co/7bn2vC6"
        dispatcher.utter_message(text="La sección e-commerce cuenta con productos y un buscardor.")
        dispatcher.utter_message(image=url_imagen)
        url_imagen = "https://ibb.co/Drtg946"
        dispatcher.utter_message(text="La sección informativa muestra información sobre tu página o empresa.")
        dispatcher.utter_message(image=url_imagen)
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_2_confirmacion", False), SlotSet("pregunta_2_repetir_confirmacion", True)]

class ActionPregunta3(Action):

    def name(self) -> Text:
        return "action_pregunta_3"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 3----")
        dispatcher.utter_message(text="Finalmente llegamos al footer, que es el componente de la página encontrado al final de la misma.")
        dispatcher.utter_message(text="Este se compone por el informacion del contacto, licencias y más.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_2_confirmacion", False), SlotSet("pregunta_2_repetir_confirmacion", False), SlotSet("pregunta_3_confirmacion", True)]


class ActionPregunta3Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_3_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 3 REPETIR----")
        url_imagen = "https://ibb.co/QJ5dTX7"
        dispatcher.utter_message(text="El footer es el pie de página de tu web y en él podes modificar los datos de contacto de tu página o empresa.")
        dispatcher.utter_message(image=url_imagen)
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_3_confirmacion", False), SlotSet("pregunta_3_repetir_confirmacion", True)]

class ActionPregunta4(Action):

    def name(self) -> Text:
        return "action_pregunta_4"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 4----")
        dispatcher.utter_message(text="Al crear una página, los componentes encabezado y footer ya estarán incluídos pero las secciones no. Para agregar una nueva sección a tu página deberás pedirmelo.")
        dispatcher.utter_message(text="Esto no quita el hecho de que puedan modificarse. En cualquier momento podes pedirme que modifique el encabezado, el footer o una sección.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_3_confirmacion", False), SlotSet("pregunta_3_repetir_confirmacion", False), SlotSet("pregunta_4_confirmacion", True)]


class ActionPregunta4Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_4_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 4 REPETIR----")
        dispatcher.utter_message(text="Todos los componentes de una página pueden ser modificados una vez creados")
        dispatcher.utter_message(text="Encabezado: Puedes modificar su logotipo y el color del título.")
        dispatcher.utter_message(text="Sección informativa: Podes modificar su título y contenido, modificando el texto o agregando imágenes.")
        dispatcher.utter_message(text="Footer: Podes modificar tus datos de contacto (e-mail y ubicación)")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_4_confirmacion", False), SlotSet("pregunta_4_repetir_confirmacion", True)]

class ActionTerminarTutorial(Action):

    def name(self) -> Text:
        return "action_terminar_tutorial"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print("(" + threading.current_thread().getName() + ") " + "----ACTION TERMINAR TUTORIAL----")
        dispatcher.utter_message(text="¡Felicitaciones " + str(tracker.get_slot("nombre_usuario")) + ", terminaste el tutorial! Ya estas listo para crear tu primera página web")
        dbm.set_user_tutorial(tracker.sender_id)
        return [SlotSet("pregunta_4_confirmacion", False), SlotSet("pregunta_4_repetir_confirmacion", False), SlotSet("pregunta_tutorial", False), SlotSet("inicia_tutorial", False)]


class ActionAvisame(Action):

    def name(self) -> Text:
        return "action_avisame"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Perfecto, cualquier cosa que necesites no dudes en pedirmelo.")
        slots = tracker.slots
        # Lista para almacenar los eventos de SlotSet
        events = []

        for slot, value in slots.items():
            if value is True:
                # Si el valor del slot es True, añadir un evento para ponerlo en False
                events.append(SlotSet(slot, False))

        # Devolver los eventos de SlotSet
        return events