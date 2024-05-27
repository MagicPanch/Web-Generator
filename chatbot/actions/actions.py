import re
import threading
from io import BytesIO

import pandas as pd
from numpy import nan

from generator.objects.sections.EcommerceSection import EcommerceSection
from generator.objects.sections.InformativeSection import InformativeSection
from generator.PageManager import PageManager
from generator.TelegramBotManager import TelegramBotManager
from generator.ReactGenerator import ReactGenerator
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import datetime
from database.DBManager import DBManager
from resources import CONSTANTS


slots_crear_pagina = ['creando_pagina', 'pregunta_nombre']
slots_crear_seccion = ['creando_seccion']
creando_pagina = False

#Actions Pagina
class ActionCapturarCreacion(Action):

    def name(self) -> Text:
        return "action_capturar_creacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR CREACION----")
        dbm = DBManager.get_instance()
        tuto = dbm.get_user_tutorial(tracker.sender_id)
        if tuto:
            seccion = tracker.get_slot('componente')
            if seccion:
                return [FollowupAction("action_capturar_tipo_seccion"), SlotSet("creando_seccion", True)]
            else:
                return [FollowupAction("action_preguntar_nombre_pagina"), SlotSet("creando_pagina", True)]
        else:
            dispatcher.utter_message(text="Para crear una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

class ActionPreguntarNombrePagina(Action):

    def name(self):
        return "action_preguntar_nombre_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTAR NOMBRE PAGINA----")
        dbm = DBManager.get_instance()
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
        global creando_pagina
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
                dbm = DBManager.get_instance()
                if creando_pagina:
                    page = PageManager.get_page(user_id, page_name)
                    message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page.get_page_address()
                    dispatcher.utter_message(text=message)
                    message = "Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password()
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
                    PageManager.add_page(user_id, page_name)

                    #Se crea en un nuevo hilo el proyecto de la pagina
                    PageManager.create_project(user_id, page_name)
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
        global creando_pagina
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR DEV----")
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))

        #Se espera a que el hilo finalice
        PageManager.join_thread(page.get_user(), page.get_name())

        #Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
        PageManager.run_dev(page.get_user(), page.get_name())

        #Esperar a que la pagina este lista
        page.wait_for_ready()
        message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page.get_page_address()
        print("(" + threading.current_thread().getName() + ") " + "--------message: ", message)
        dispatcher.utter_message(text=message)

        message = "Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password()
        print("(" + threading.current_thread().getName() + ") " + "--------message: ", message)
        dispatcher.utter_message(text=message)
        print("(" + threading.current_thread().getName() + ") " + "--------Despues de utter_message")
        events = []
        for slot in slots_crear_pagina:
            events.append(SlotSet(slot, False))
        return events

class ActionEjecutarPagina(Action):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR PAGINA----")
        dbm = DBManager.get_instance()
        tuto = dbm.get_user_tutorial(tracker.sender_id)
        if tuto:
            if tracker.get_slot('page_name') is None:
                message = "Indicame el nombre de la pagina que deseas ejecutar. Te recuerdo que tus paginas son: "
                pags = dbm.get_user_pages(tracker.sender_id)
                for pag in pags:
                    message += str(pag['name']) + "\n"
                return [SlotSet("pregunta_ejecucion", True)]
            else:
                # Se estuvo hablando de una pagina en particular
                page_doc = dbm.get_page(tracker.sender_id, tracker.get_slot('page_name'))
                print("(" + threading.current_thread().getName() + ") " + "--------page_doc: ", page_doc)
                if not page_doc:
                    # Esa pagina no pertenece al usuario
                    message = "No se encuentra la pagina que deseas ejecutar. Te recuerdo que tus paginas son:\n"
                    pags = dbm.get_user_pages(tracker.sender_id)
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
                            dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password())
                            return []
                        elif page_obj.is_running_dev():
                        # Se esta ejecutando en modo dev
                            PageManager.stop_page(tracker.sender_id, page_doc.name)
                            PageManager.stop_tunnel(tracker.sender_id, page_doc.name)
                            page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)
                            print("(" + threading.current_thread().getName() + ") " + "------------page_obj: ", page_obj)
                    else:
                    # La pagina no vive en PageManager
                        page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)

                    #Verificar si esta compilada
                    if not dbm.was_compiled(tracker.sender_id, page_doc.name):
                        print("(" + threading.current_thread().getName() + ") " + "----------------pagina no compilada")
                        PageManager.build_project(tracker.sender_id, page_doc.name)
                        dbm.set_compilation_date(tracker.sender_id, page_doc.name)
                        PageManager.join_thread(tracker.sender_id, page_doc.name)
                        print("(" + threading.current_thread().getName() + ") " + "------------PAGINA COMPILADA")
                    else:
                        print("(" + threading.current_thread().getName() + ") " + "----------------pagina ya compilada")

                    # Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
                    PageManager.run_project(tracker.sender_id, page_doc.name)
                    page_obj.wait_for_ready()

                    page_address = page_obj.get_page_address()
                    print("(" + threading.current_thread().getName() + ") " + "------------page_address: ", page_address)
                    dispatcher.utter_message(text="Podes acceder a tu página en el siguiente link: " + page_address)
                    dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password())
                    return [SlotSet("pregunta_ejecucion", False)]
        else:
            dispatcher.utter_message(text="Para ejecutar una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

    class ActionDetenerPagina(Action):

        def name(self) -> Text:
            return "action_detener_pagina"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            print("(" + threading.current_thread().getName() + ") " + "----ACTION DETENER PAGINA----")
            last_message_entities = tracker.get_latest_entity_values("text")
            print("(" + threading.current_thread().getName() + ") " + "--------last_message_entities: ", last_message_entities)

            dbm = DBManager.get_instance()
            tuto = dbm.get_user_tutorial(tracker.sender_id)
            if tuto:
                if "page_name" in last_message_entities:
                    # Se especifico una pagina en el ultimo mensaje
                    PageManager.stop_page(tracker.sender_id, tracker.get_latest_entity_values('page_name'))
                    PageManager.stop_tunnel(tracker.sender_id, tracker.get_latest_entity_values('page_name'))
                    PageManager.pop_page(tracker.sender_id, tracker.get_latest_entity_values('page_name'))
                    print("(" + threading.current_thread().getName() + ") " + "------------PAGINA DETENIDA CON EXITO------------")
                    dispatcher.utter_message(text="Tu pagina fue apagada con exito.")
                elif "todas" in tracker.latest_message.get("text"):
                    # Quiere detener todas

                    for pag in PageManager.get_user_running_pages(tracker.sender_id):
                        PageManager.stop_page(tracker.sender_id, pag.get_name())
                        PageManager.stop_tunnel(tracker.sender_id, pag.get_name())
                        PageManager.pop_page(tracker.sender_id, pag.get_name())
                        dispatcher.utter_message(text="La pagina " + pag.get_name() + " fue detenida con éxito.")
                    print("(" + threading.current_thread().getName() + ") " + "------------PAGINAS DETENIDA CON EXITO------------")
                else:
                    #No especifico cual quiere detener pero hay slot de contexto
                    page_name = tracker.get_slot('page_name')
                    if page_name:
                        PageManager.stop_page(tracker.sender_id, page_name)
                        PageManager.stop_tunnel(tracker.sender_id, page_name)
                        PageManager.pop_page(tracker.sender_id, page_name)
                        print("(" + threading.current_thread().getName() + ") " + "------------PAGINA DETENIDA CON EXITO------------")
                        dispatcher.utter_message(text="Tu pagina fue apagada con exito.")
                    else:
                        message = "Indicame el nombre de la pagina que deseas detener. Te recuerdo que tus paginas en ejecución son: \n"
                        pags = PageManager.get_user_running_pages(tracker.sender_id)
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
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR EDICION----")
        dbm = DBManager.get_instance()
        tuto = dbm.get_user_tutorial(tracker.sender_id)
        if tuto:
            last_message_intent = tracker.latest_message.get('intent').get('name')
            print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
            if "modificar_pagina" in last_message_intent and not tracker.get_slot("agregando_productos"):
                componente = tracker.get_slot('componente')
                page_name = tracker.get_slot('page_name')
                if page_name and componente:
                # Hay pagina y componente a editar
                    print("(" + threading.current_thread().getName() + ") " + "--------componente: ", componente)
                    print("(" + threading.current_thread().getName() + ") " + "--------pagina: ", page_name)

                    page_doc = dbm.get_page(tracker.sender_id, tracker.get_slot('page_name'))
                    print("(" + threading.current_thread().getName() + ") " + "--------page_doc: ", page_doc)
                    if not page_doc:
                        # Esa pagina no pertenece al usuario
                        message = "La pagina que estas intentando modificar no te pertenece. Te recuerdo que tus paginas son: "
                        pags = dbm.get_user_pages(tracker.sender_id)
                        for pag in pags:
                            message += str(pag.name) + "\n"
                        dispatcher.utter_message(text=message)
                        return [SlotSet("pregunta_nombre", True)]
                    else:
                        # La pagina pertenece al usuario
                        print("(" + threading.current_thread().getName() + ") " + "------------la pagina es del usuario")
                        page_obj = PageManager.get_page(tracker.sender_id, page_doc.name)
                        if not page_obj:
                            print("(" + threading.current_thread().getName() + ") " + "------------no hay page_obj")
                            page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)
                            PageManager.run_dev(tracker.sender_id, page_doc.name)
                            page_obj.wait_for_ready()
                            page_address = page_obj.get_page_address()
                            dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_address)
                            dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password())
                        else:
                            print("(" + threading.current_thread().getName() + ") " + "------------hay page_obj")
                            if page_obj.is_running():
                                print("(" + threading.current_thread().getName() + ") " + "------------la pagina esta corriendo")
                                PageManager.switch_dev(tracker.sender_id, page_doc.name)
                                page_address = page_obj.get_page_address()
                                dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_address)
                                dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password())
                            elif not page_obj.is_running_dev():
                                PageManager.run_dev(tracker.sender_id, page_doc.name)
                                page_obj.wait_for_ready()
                                page_address = page_obj.get_page_address()
                                dispatcher.utter_message(
                                    text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_address)
                                dispatcher.utter_message(
                                    text="Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password())
                        if componente.lower() == "encabezado":
                            return[FollowupAction("action_preguntar_color_encabezado"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                        elif componente.lower() == "footer":
                            return[FollowupAction("action_preguntar_mail_footer"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                        elif componente.lower() == "seccion":
                        # Va a editar una seccion
                            tipo_seccion = tracker.get_slot('tipo_seccion')
                            print("(" + threading.current_thread().getName() + ") " + "--------tipo_seccion: ", tipo_seccion)
                            nombre_seccion = tracker.get_slot('nombre_informativa')
                            print("(" + threading.current_thread().getName() + ") " + "--------nombre_informativa: ", nombre_seccion)
                            secciones = dbm.get_page_sections(tracker.sender_id, tracker.get_slot('page_name'))
                            if len(secciones) > 0:
                            # La pagina tiene secciones
                                if nombre_seccion:
                                    for seccion in secciones:
                                        if seccion.title == nombre_seccion.lower():
                                            return [SlotSet("nombre_seccion_editando", nombre_seccion),
                                                    FollowupAction("action_modificar_informativa_1"),
                                                    SlotSet("pregunta_componente", False),
                                                    SlotSet("pregunta_nombre", False),
                                                    SlotSet("pregunta_edicion", False)]
                                elif tipo_seccion:
                                # Hay tipo seccion
                                    for seccion in secciones:
                                        print(seccion.title)
                                        if seccion.title.lower() == tipo_seccion.lower():
                                            if "e-commerce" in tipo_seccion.lower():
                                                return [FollowupAction("action_modificar_ecommerce"),
                                                        SlotSet("pregunta_componente", False),
                                                        SlotSet("pregunta_nombre", False),
                                                        SlotSet("pregunta_edicion", False)]
                                            elif "informativa" in tipo_seccion.lower():
                                                return [FollowupAction("action_modificar_informativa"),
                                                        SlotSet("pregunta_componente", False),
                                                        SlotSet("pregunta_nombre", False),
                                                        SlotSet("pregunta_edicion", False)]
                                    else:
                                        dispatcher.utter_message(text=str(tipo_seccion) + " no es un tipo de seccion válido. Te recuerdo que las secciones a crear son: \n E-Commerce \n Informativa")
                                        return [SlotSet("pregunta_componente", True), SlotSet("pregunta_seccion", True)]
                                else:
                                # No hay tipo seccion
                                    message = "¿Que sección te gustaría modificar? Te recuerdo que las secciones de tu pagina son:\n"
                                    for seccion in secciones:
                                        message += seccion.title + "\n"
                                    dispatcher.utter_message(text=message)
                                    return [SlotSet("pregunta_componente", True), SlotSet("pregunta_seccion", True)]
                            else:
                            # La pagina no tiene secciones
                                dispatcher.utter_message(text="La pagina " + page_doc.name + " no cuenta con ninguna sección, por lo que antes deberás crear una.")
                                return [FollowupAction("action_capturar_tipo_seccion")]
                elif page_name and not componente:
                # Hay pagina y no hay componente a editar
                    print("(" + threading.current_thread().getName() + ") " + "--------pagina: ", page_name)
                    message = "Que componente quisieras editar? Te recuerdo que los componentes son: \n"
                    message += "Encabezado \n"
                    message += "Seccion \n"
                    message += "Footer \n"
                    dispatcher.utter_message(text=message)
                    return [SlotSet("pregunta_componente", True)]
                elif not page_name and componente:
                # No hay pagina y hay componente a editar
                    print("(" + threading.current_thread().getName() + ") " + "--------componente: ", componente)
                    message = "Indicame el nombre de la pagina que deseas modificar. Te recuerdo que tus paginas son: \n"
                    pags = dbm.get_user_pages(tracker.sender_id)
                    for pag in pags:
                        message += str(pag.name) + "\n"
                    dispatcher.utter_message(text=message)
                    return [SlotSet("pregunta_nombre", True)]
                else:
                # No hay pagina ni componente
                    message = "Indicame el nombre de la pagina que deseas modificar. Te recuerdo que tus paginas son: \n"
                    pags = dbm.get_user_pages(tracker.sender_id)
                    for pag in pags:
                        message += str(pag.name) + "\n"
                    dispatcher.utter_message(text=message)
                    message = "\n Además necesito que me proporciones el componente que quieras editar. Ellos pueden ser: \n"
                    message += "Encabezado \n"
                    message += "Seccion \n"
                    message += "Footer \n"
                    dispatcher.utter_message(text=message)
                    return [SlotSet("pregunta_edicion", True)]
            elif "agregar_producto" in last_message_intent or tracker.get_slot("agregando_productos"):
                page_name = tracker.get_slot('page_name')
                if page_name:
                    page_doc = dbm.get_page(tracker.sender_id, tracker.get_slot('page_name'))
                    print("(" + threading.current_thread().getName() + ") " + "--------page_doc: ", page_doc)
                    if not page_doc:
                        # Esa pagina no pertenece al usuario
                        message = "La pagina en la que estas intentando agregar productos no te pertenece. Te recuerdo que tus paginas son: "
                        pags = dbm.get_user_pages(tracker.sender_id)
                        for pag in pags:
                            message += str(pag.name) + "\n"
                        dispatcher.utter_message(text=message)
                        return [SlotSet("pregunta_nombre", True)]
                    else:
                        # La pagina pertenece al usuario
                        print("(" + threading.current_thread().getName() + ") " + "------------la pagina es del usuario")
                        page_obj = PageManager.get_page(tracker.sender_id, page_doc.name)
                        if not page_obj:
                            page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)
                        if page_obj.has_ecomm_section():
                            return [SlotSet("agregando_productos", True), FollowupAction("action_pedir_productos")]
                        else:
                            message = "La pagina " + str(page_name) + " no cuenta con una sección e-commerce. Te recuerdo que tus paginas con sección e-commerce son: \n"
                            pags = dbm.get_user_pages(tracker.sender_id)
                            for pag in pags:
                                print(pag)
                                if pag.has_ecomm_section:
                                    message += str(pag.name) + "\n"
                            dispatcher.utter_message(text=message)
                            return [SlotSet("pregunta_nombre", True)]
                else:
                    pags = dbm.get_user_pages(tracker.sender_id)
                    if pags:
                        message = "Indicame el nombre de la pagina en la que deseas agregar productos. Te recuerdo que tus paginas con sección e-commerce son: \n"
                        for pag in pags:
                            if pag.has_ecomm_section:
                                message += str(pag.name) + "\n"
                    else:
                        message = "Parece que ninguna de tus páginas tiene una sección e-commerce. Deberas agregar una a la página que deseas agregar productos."
                    dispatcher.utter_message(text=message)
                    return [SlotSet("pregunta_nombre", True)]
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
            message = "Bueno, podemos ver el tipo mas tarde"
        else:
            message = "Perfecto! Ya se guardo que color queres, el cual sera: \n" + str(color) + "."
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
        print("(" + threading.current_thread().getName() + ") " + "----EN ACTION RECIBIR IMAGEN----")
        print("(" + threading.current_thread().getName() + ") " + "--------creando_encabezado ", tracker.get_slot("creando_encabezado"))
        print("(" + threading.current_thread().getName() + ") " + "--------creando_seccion_informativa ", tracker.get_slot("creando_seccion_informativa"))
        print("(" + threading.current_thread().getName() + ") " + "--------pregunta_otra_imagen_seccion_informativa ", tracker.get_slot("pregunta_otra_imagen_seccion_informativa"))
        print("(" + threading.current_thread().getName() + ") " + "--------last_message_intent: ", tracker.latest_message.get('intent').get('name'))
        telegram_bot = TelegramBotManager.get_instance()
        dbm = DBManager.get_instance()

        # Verifica si el último mensaje contiene una imagen
        latest_message = tracker.latest_message
        if 'photo' in latest_message['metadata']['message']:
            error = False
            photo = latest_message['metadata']['message']['photo'][1]
            image_id = photo['file_id']
            page_path = PageManager.get_page_path(tracker.sender_id, tracker.get_slot("page_name"))
            if not image_id:
                error = True
            else:
                if tracker.get_slot("creando_encabezado"):
                    PageManager.go_to_main_dir()
                    telegram_bot.download_image(page_path=page_path, subdir="components", image_id=image_id, image_name="logo.png")
                elif tracker.get_slot("creando_seccion_informativa"):
                    PageManager.go_to_main_dir()
                    telegram_bot.download_image(page_path=page_path, subdir="sect_inf_images", image_id=image_id, image_name=(photo["file_unique_id"] + ".png"))
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

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ")" + "----EN ACTION CREAR ENCABEZADO----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        page_path = PageManager.get_page_path(tracker.sender_id, tracker.get_slot('page_name'))
        print("(" + threading.current_thread().getName() + ")" + "--------page_path: ", page_path)
        color = tracker.get_slot('color_encabezado')
        print("(" + threading.current_thread().getName() + ")" + "--------color: ", color)
        dataHeader = {
            "titulo": tracker.get_slot('page_name'),
            "address": page_path,
            "addressLogo": "./logo.png",
            "colorTitulo": color
        }
        PageManager.go_to_main_dir()
        ReactGenerator.generarHeader(dataHeader)
        print("-------------ENCABEZADO MODIFICADO-------------")
        dbm = DBManager.get_instance()
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
        print("(" + threading.current_thread().getName() + ") " + "----ACTION GUARDAR MAIL FOOTER----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        last_message_intent = tracker.latest_message.get('intent').get('name')
        print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
        if 'decir_mail' in last_message_intent:
        #El usuario proporciono el mail
            mail = tracker.get_slot('mail')
            print("(" + threading.current_thread().getName() + ") " + "------------mail: ", mail)
            #Guardar el mail en la pagina
            dbm = DBManager.get_instance()
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
        print("(" + threading.current_thread().getName() + ") " + "----ACTION GUARDAR UBICACION FOOTER----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        last_message_intent = tracker.latest_message.get('intent').get('name')
        print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
        if 'decir_ubicacion' in last_message_intent:
        #El usuario proporciono su ubicacion
            ubicacion = tracker.get_slot("ubicacion")
            print("(" + threading.current_thread().getName() + ") " + "------------ubicacion: ", ubicacion)
            #Guardar la ubicacion en la pagina
            dbm = DBManager.get_instance()
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
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR FOOTER----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
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
        PageManager.go_to_main_dir()
        ReactGenerator.generarFooter(dataFooter)
        print("-------------FOOTER MODIFICADO-------------")
        dispatcher.utter_message(text="Podes ver los cambios que realizamos en el footer")
        return [SlotSet("creando_footer", False), SlotSet("componente", None)]

# SECCIONES

## CREAR
class ActionCapturarTipoSeccion(Action):
    def name(self) -> Text:
        return "action_capturar_tipo_seccion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR TIPO SECCION----")
        page_name = tracker.get_slot("page_name")
        print("(" + threading.current_thread().getName() + ") " + "--------page_name: ", page_name)
        dbm = DBManager.get_instance()
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
                page_obj = PageManager.get_page(tracker.sender_id, page_doc.name)
                if not page_obj:
                    page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)
                print("(" + threading.current_thread().getName() + ") " + "--------page_obj.name: ", page_obj.get_name())
                if not tracker.get_slot('tipo_seccion') == "e-commerce":
                    if not page_obj.is_running_dev():
                        PageManager.run_dev(tracker.sender_id, page_doc.name)
                        page_obj.wait_for_ready()
                        message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address()
                        dispatcher.utter_message(text=message)
                        message = "Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password()
                        dispatcher.utter_message(text=message)
                    elif page_obj.is_running():
                        PageManager.switch_dev(tracker.sender_id, page_doc.name)
                        message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address()
                        dispatcher.utter_message(text=message)
                        message = "Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password()
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
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION E-COMMERCE----")
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot("page_name"))
        seccion = page.get_section("ecommerce")
        if seccion:
            dispatcher.utter_message(text="Tu página ya tiene una sección de e-commerce.")
        else:
            page.add_section(EcommerceSection())

            if page.is_running() or page.is_running_dev():
                PageManager.stop_page(tracker.sender_id, page.get_name())
                PageManager.stop_tunnel(tracker.sender_id, page.get_name())
            PageManager.add_ecommerce(tracker.sender_id, tracker.get_slot("page_name"))
            PageManager.join_thread(tracker.sender_id, tracker.get_slot("page_name"))
            #ReactGenerator.generarEcommerce()
            PageManager.run_dev(page.get_user(), page.get_name())
            page.wait_for_ready()
            message = "Tu pagina se encuentra en modo edición. Podrás visualizar la nueva sección en: " + page.get_page_address()
            dispatcher.utter_message(text=message)
            message = "Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password()
            dispatcher.utter_message(text=message)
            #ReactGenerator.generarEcommerce()
            dbm = DBManager.get_instance()
            dbm.add_ecomm_section(tracker.sender_id, tracker.get_slot("page_name"))
        return [SlotSet("pregunta_seccion", False), SlotSet("creando_seccion", False), SlotSet("componente", None)]

#### AGREGAR PRODUCTOS

class ActionPedirProductos(Action):

    def name(self) -> Text:
        return "action_pedir_productos"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PEDIR PRODUCTOS----")
        telegram_bot = TelegramBotManager.get_instance()
        message = "Podes agregar los productos de a uno o cargar múltiples productos en un archivo de datos y enviármelo. Si optas por la carga mediante archivo, completa la siguiente planilla agregando los datos en una nueva fila. En los campos \"multimedia\" coloca el link a las imágenes o videos del producto"
        dispatcher.utter_message(text=message)
        PageManager.go_to_main_dir()
        telegram_bot.send_file_to_user(tracker.sender_id, CONSTANTS.TEMPLATE_PRODUCTOS_DIR)
        dispatcher.utter_message(text="Si vas a cargar los productos de a uno voy a necesitar los siguientes datos:")
        dispatcher.utter_message(text="Cantidad:\nTitulo:\nDescripción:\nPrecio:")
        return [SlotSet("pregunta_carga", True)]

class ActionCapturarProductoCargado(Action):

    def name(self) -> Text:
        return "action_capturar_producto_cargado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR PRODUCTO CARGADO----")
        # Verifica si el último mensaje contiene una imagen
        latest_message = tracker.latest_message
        dbm = DBManager.get_instance()
        if 'document' in latest_message['metadata']['message']:
            error = False
            documento = latest_message['metadata']['message']['document']
            telegram_bot = TelegramBotManager.get_instance()
            file_id = documento['file_id']
            if not documento:
                error = True
            else:
                file = telegram_bot.get_csv_file(file_id)
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
            if error:
                dispatcher.utter_message(text="No se pudo recibir el archivo. Por favor envíalo nuevamente.")
            return []
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
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 2----")
        print("(" + threading.current_thread().getName() + ") " + "--------page_name: ", tracker.get_slot('page_name'))
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))
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
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 3----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')
        last_user_message = str(tracker.latest_message.get('text'))
        text = last_user_message[3:len(last_user_message) - 3].strip()
        if tracker.get_slot("nombre_informativa"):
            nombre_informativa = tracker.get_slot("nombre_informativa")
        else:
            nombre_informativa = "Informacion"
        page = PageManager.get_page(user_id, page_name)
        inf_section = page.get_section(nombre_informativa)
        inf_section.set_text(text)
        dispatcher.utter_message(text="Texto informativo guardado.")
        dbm = DBManager.get_instance()
        dbm.add_inf_section(user_id, page_name, inf_section)
        PageManager.go_to_main_dir()
        ReactGenerator.agregarSectionInformativa(nombre_informativa, PageManager.get_page_path(user_id, page_name), inf_section.get_text())
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


    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION MODIFICAR SECCION INFORMATIVA 2----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')
        last_user_message = str(tracker.latest_message.get('text'))
        text = last_user_message[3:len(last_user_message) - 3].strip()
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        nombre_informativa = tracker.get_slot("nombre_informativa")
        inf_section = page.get_section(nombre_informativa)
        inf_section.set_text(text)
        dispatcher.utter_message(text="Texto informativo guardado.")
        dbm = DBManager.get_instance()
        dbm.updt_inf_section(user_id, page_name, nombre_informativa, text)
        PageManager.go_to_main_dir()
        ReactGenerator.modificarSectionInformativa(nombre_informativa, PageManager.get_page_path(), text)
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("editando_seccion_informativa", False), SlotSet("pide_text_informativa", False)]


class ActionModificarInformativa4(Action):

    def name(self) -> Text:
        return "action_modificar_informativa_4"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION MODIFICAR SECCION INFORMATIVA 4----")
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        if tracker.get_slot("nombre_informativa"):
            nombre_informativa = tracker.get_slot("nombre_informativa")
        else:
            nombre_informativa = tracker.get_slot("nombre_seccion_editando")
        inf_section = page.get_section(nombre_informativa)
        dbm = DBManager.get_instance()
        dbm.updt_inf_section(tracker.sender_id, tracker.get_slot("page_name"), tracker.get_slot("nombre_seccion_editando"),  inf_section)
        #ReactGenerator.generarSeccionInformativa()
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("editando_seccion_informativa", False)]

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
        dbm = DBManager.get_instance()
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


    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dbm = DBManager.get_instance()
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
        print("(" + threading.current_thread().getName() + ") " + "----ACTION TERMINAR TUTORIAL----")
        dispatcher.utter_message(text="¡Felicitaciones " + str(tracker.get_slot("nombre_usuario")) + ", terminaste el tutorial! Ya estas listo para crear tu primera página web")
        dbm = DBManager.get_instance()
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