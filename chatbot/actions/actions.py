import threading

from generator.Objects.InformativeSection import InformativeSection
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
        tuto = DBManager.get_user_tutorial(DBManager.get_instance(), tracker.sender_id)
        if tuto:
            dispatcher.utter_message(text="¿Como queres que se llame tu pagina? Por favor indica su nombre en el siguiente formato: www. nombre-pagina .com")
            return [SlotSet("creando_pagina", True)]
        else:
            dispatcher.utter_message(text="Para crear una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR PAGINA----")
        print("(" + threading.current_thread().getName() + ") " + "--------page_name_slot: ", tracker.get_slot('page_name'))
        entities = tracker.latest_message.get("entities", [])
        # Filtrar las entidades para obtener solo las de tipo "page_name"
        page_name_entities = [entity["value"] for entity in entities if entity["entity"] == "page_name"]
        # Obtener el último valor de la lista de entidades de tipo "page_name" (si existe)
        if page_name_entities:
            last_page_name = page_name_entities[-1]
            print("(" + threading.current_thread().getName() + ") " + "--------page_name_entity: ", last_page_name)
        print("(" + threading.current_thread().getName() + ") " + "--------creando_pagina: ", tracker.get_slot("creando_pagina"))



        last_message_intent = tracker.latest_message.get('intent').get('name')
        if 'denegar' in last_message_intent:
            dispatcher.utter_message(text="Entendido, si mas tarde deseas retomar la creacion de tu pagina puedes pedirmelo.")
            return [SlotSet("creando_pagina", False)]

        if tracker.get_slot("creando_pagina"):
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

                    dispatcher.utter_message(text="Aguarda un momento mientras se crea tu página. Este proceso puede demorar unos minutos.")
                    return [SlotSet("creando_pagina", False), FollowupAction("action_ejecutar_dev")]
                else:
                    #La pagina ya existe
                    dispatcher.utter_message(text="Ya existe una pagina con ese nombre. Por favor elige otro.")
                    return [SlotSet("creando_pagina", True)]
        else:
            return []

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
                message = "No se encuentra la pagina que deseas modificar. Te recuerdo que tus paginas son: \n"
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
                    if page_obj.is_running_dev():
                        print("(" + threading.current_thread().getName() + ") " + "--------la pagina esta running dev")
                        return [SlotSet("pregunta_modificacion", False)]
                    else:
                        print("(" + threading.current_thread().getName() + ") " + "--------la pagina no esta running dev")
            return [SlotSet("pregunta_modificacion", False), FollowupAction("action_ejecutar_dev")]


class ActionEjecutarDev(Action):

    def name(self) -> Text:
        return "action_ejecutar_dev"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR DEV----")
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        #dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page.get_page_address())

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
        return [SlotSet("running_dev", True)]


class ActionEjecutarPagina(Action):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION EJECUTAR PAGINA----")
        tuto = DBManager.get_user_tutorial(DBManager.get_instance(), tracker.sender_id)
        if tuto:
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

            tuto = DBManager.get_user_tutorial(DBManager.get_instance(), tracker.sender_id)
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
                        return [SlotSet("pregunta_ejecucion", True)]
                return []
            else:
                dispatcher.utter_message(text="Para detener una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
                return [SlotSet("pregunta_tutorial", True)]

class ActionCapturarEdicion(Action):

    def name(self) -> Text:
        return "action_capturar_edicion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CAPTURAR EDICION----")
        tuto = DBManager.get_user_tutorial(DBManager.get_instance(), tracker.sender_id)
        if tuto:
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
                    if not page_obj:
                        page_obj = PageManager.add_page(tracker.sender_id, page_doc.name)
                        PageManager.run_dev(tracker.sender_id, page_doc.name)
                        page_address = page_obj.get_page_address()
                        dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_address)
                        dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password())
                    else:
                        if page_obj.is_running():
                            PageManager.switch_dev(tracker.sender_id, page_doc.name)
                            page_address = page_obj.get_page_address()
                            dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_address)
                            dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + PageManager.get_tunnel_password())
                    if componente.lower() == "encabezado":
                        return[FollowupAction("action_preguntar_color_encabezado"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                    elif componente.lower() == "footer":
                        return[FollowupAction("action_preguntar_mail_footer"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                    elif componente.lower() == "seccion":
                    # Va a editar una seccion
                        tipo_seccion = tracker.get_slot('tipo_seccion')
                        print("(" + threading.current_thread().getName() + ") " + "--------tipo_seccion: ", tipo_seccion)
                        if tipo_seccion:
                        # Hay tipo seccion
                            if tipo_seccion.lower() == "e-commerce":
                                return [FollowupAction("action_crear_ecommerce"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                            elif tipo_seccion.lower() == "informativa":
                                return [FollowupAction("action_crear_informativa_1"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                            elif tipo_seccion.lower() == "abm":
                                return [FollowupAction("action_crear_abm"), SlotSet("pregunta_componente", False), SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
                            else:
                                dispatcher.utter_message(text=str(tipo_seccion) + " no es un tipo de seccion válido. Te recuerdo que las secciones a crear son: \n E-Commerce \n Informativa \n ABM.")
                                return [SlotSet("pregunta_componente", True), SlotSet("pregunta_seccion", True)]
                        else:
                        # No hay tipo seccion
                            dispatcher.utter_message(text="¿Que sección te gustaría crear o modificar? Te recuerdo que las secciones a crear son: \n E-Commerce \n Informativa \n ABM.")
                            return [SlotSet("pregunta_componente", True), SlotSet("pregunta_seccion", True)]
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
        else:
            dispatcher.utter_message(text="Para modificar una pagina primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]


'''
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
        print("(" + threading.current_thread().getName() + ") " + "----EN ACTION GUARDAR SECCION----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
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
        print("(" + threading.current_thread().getName() + ") " + "----EN ACTION CREAR SECCION----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        page_path = PageManager.get_page_path(tracker.sender_id, tracker.get_slot('page_name'))
        dataSection = {}
        #ReactGenerator.generarSection(dataSection)
        print("-------------SECCION CREADA-------------")
        dispatcher.utter_message(text="Podes ver la nueva sección en tu página")
        return [SlotSet("creando_seccion", False)]
'''

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

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
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
            if not image_id:
                error = True
            else:
                if tracker.get_slot("creando_encabezado"):
                    await PageManager.download_telegram_image(PageManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), subdir="components", image_id=image_id, image_name="logo")
                elif tracker.get_slot("creando_seccion_informativa"):
                    await PageManager.download_telegram_image(PageManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'), subdir="sect_inf_images", image_id=image_id, image_name=photo["file_unique_id"])
            if not error:
                dispatcher.utter_message(text="Imagen recibida con éxito.")
                if tracker.get_slot("creando_seccion_informativa"):
                    dispatcher.utter_message(text="¿Queres agregar otra imagen?")
                    return [SlotSet("pregunta_otra_imagen_seccion_informativa", True)]
            else:
                dispatcher.utter_message(text="No se pudo procesar la imagen.")
        else:
            if tracker.latest_message.get('intent').get('name') == "denegar":
                if tracker.get_slot("creando_encabezado"):
                    dispatcher.utter_message(text="Perfecto, el encabezado de tu página no contendrá ningún logo")
                elif tracker.get_slot("creando_seccion_informativa"):
                    return [SlotSet("pregunta_otra_imagen_seccion_informativa", False)]
        return []

class ActionPreguntarColorEncabezado(Action):
    def name(self) -> Text:
        return "action_preguntar_color_encabezado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="De que color te gustaria que sea el encabezado? Para ello necesito que me proveas su codigo hexadecimal. Podes seleccionar tu color y copiar su codigo en el siguiente link: https://g.co/kgs/FMBcG8K")
        return [SlotSet("creando_encabezado", True), FollowupAction("action_listen")]


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
        DBManager.updt_modification_date(DBManager.get_instance(), tracker.sender_id, tracker.get_slot('page_name'))
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
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
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
        return [SlotSet("creando_encabezado", False), SlotSet("componente", None)]

# SECCIONES

## INFORMATIVA

class ActionCrearInformativa1(Action):

    def name(self) -> Text:
        return "action_crear_informativa_1"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 1----")
        dispatcher.utter_message(text="¿Que nombre llevará la sección?")
        return [SlotSet("creando_seccion_informativa", True)]


class ActionCrearInformativa2(Action):

    def name(self) -> Text:
        return "action_crear_informativa_2"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 2----")
        last_message_intent = tracker.latest_message.get('intent').get('name')
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        nombre_informativa = "Informacion"
        if "decir_nombre_informativa" in last_message_intent:
            nombre_informativa = tracker.get_slot("nombre_informativa")
            dispatcher.utter_message(text="Nombre de sección guardado.")
        inf_section = InformativeSection(nombre_informativa)
        page.add_section(inf_section)
        dispatcher.utter_message(text="Proporcioname texto el informativo. Por favor, respeta el siguiente formato:")
        dispatcher.utter_message(text="###\nTexto\n###")
        dispatcher.utter_message(text="Si deseas agregar múltiples bloques de texto, envíalos en el mismo mensaje respetando el siguiente formato:")
        dispatcher.utter_message(text="###\nTitulo texto1\n##\nTexto1\n##\nTitulo texto2\n##\nTexto2\n##\n###")
        return [SlotSet("creando_seccion_informativa", True)]


class ActionCrearInformativa3(Action):

    def name(self) -> Text:
        return "action_crear_informativa_3"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 3----")
        last_user_message = str(tracker.latest_message.get('text'))
        text = last_user_message[3:len(last_user_message) - 3].strip()
        textos = {}
        if "##" in text:
        # El texto tiene subtitulos
            texts = text.split("##").strip()
            i = 0;
            while i < len(texts) / 2:
                textos[texts[i]] = texts[i + 1]
                i += 2
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        if tracker.get_slot("nombre_informativa"):
            nombre_informativa = tracker.get_slot("nombre_informativa")
        else:
            nombre_informativa = "Informacion"
        inf_section = page.get_section("informativa", nombre_informativa)
        if len(textos) > 0:
            inf_section.set_texts(textos)
        else:
            inf_section.set_text(text)
        dispatcher.utter_message(text="Texto informativo guardado.")
        dispatcher.utter_message(text="Si lo deseas podes enviarme alguna imagen para mostrar en tu sección. Si vas a enviar imagenes, por favor envialas de a una.")
        return [SlotSet("creando_seccion_informativa", True)]


class ActionCrearInformativa4(Action):

    def name(self) -> Text:
        return "action_crear_informativa_4"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION CREAR SECCION INFORMATIVA 4----")
        page = PageManager.get_page(tracker.sender_id, tracker.get_slot('page_name'))
        if tracker.get_slot("nombre_informativa"):
            nombre_informativa = tracker.get_slot("nombre_informativa")
        else:
            nombre_informativa = "Informacion"
        inf_section = page.get_section("informativa", nombre_informativa)
        DBManager.add_inf_section(DBManager.get_instance(), tracker.sender_id, tracker.get_slot("page_name"), inf_section)
        #ReactGenerator.generarSeccionInformativa()
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("creando_seccion_informativa", False)]

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
        user_doc = DBManager.get_user(DBManager.get_instance(), ide)
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
            DBManager.add_user(DBManager.get_instance(), ide, tracker.get_slot("usuario"), nombre)
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
        dispatcher.utter_message(text="Nuestras páginas se construyen mediante componentes. El primero de ellos es el encabezado, que se encuentra en la parte superior de la página web.")
        dispatcher.utter_message(text="Este encabezado se compone por el título de la página, el color del título y un logo.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_1_confirmacion", False), SlotSet("pregunta_1_repetir_confirmacion", True)]


class ActionPregunta2(Action):

    def name(self) -> Text:
        return "action_pregunta_2"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 2----")
        dispatcher.utter_message(text="El siguiente componente de nuestras páginas es el cuerpo, el cual dividimos según 3 tipos de secciones: e-commerce, informativa y ABM.")
        dispatcher.utter_message(text="Seccion e-commerce: ")
        dispatcher.utter_message(text="Seccion informativa: ")
        dispatcher.utter_message(text="Seccion ABM: ")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_1_confirmacion", False), SlotSet("pregunta_1_repetir_confirmacion", False), SlotSet("pregunta_2_confirmacion", True)]


class ActionPregunta2Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_2_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION PREGUNTA 2 REPETIR----")
        dispatcher.utter_message(text="El siguiente componente de nuestras páginas es el cuerpo, el cual dividimos según 3 tipos de secciones: e-commerce, informativa y ABM.")
        dispatcher.utter_message(text="Seccion e-commerce: ")
        dispatcher.utter_message(text="Seccion informativa: ")
        dispatcher.utter_message(text="Seccion ABM: ")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_2_confirmacion", False), SlotSet("pregunta_2_repetir_confirmacion", True)]


class ActionTerminarTutorial(Action):

    def name(self) -> Text:
        return "action_terminar_tutorial"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("(" + threading.current_thread().getName() + ") " + "----ACTION TERMINAR TUTORIAL----")
        dispatcher.utter_message(text="¡Felicitaciones " + str(tracker.get_slot("nombre_usuario")) + ", terminaste el tutorial! Ya estas listo para crear tu primera página web")
        DBManager.set_user_tutorial(DBManager.get_instance(), tracker.sender_id)
        return [SlotSet("pregunta_2_confirmacion", False), SlotSet("pregunta_2_repetir_confirmacion", False)]
