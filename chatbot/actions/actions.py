import re
import threading
import datetime
import pandas as pd
from io import BytesIO
from numpy import nan

from chatbot.actions.BaseAction import BaseAction
from resources import CONSTANTS, utils
from database.DBManager import DBManager
from database.collections.general.Page import Page
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

slots_crear_seccion = ['creando_seccion']
creando_pagina = False
creando_ecommerce = False
dbm = DBManager.get_instance()
pgm = PageManager.get_instance()
rg = ReactGenerator.get_instance()
tbm = TelegramBotManager.get_instance()

class ActionCapturarCreacion(BaseAction):

    def name(self) -> Text:
        return "action_capturar_creacion"

    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        seccion = tracker.get_slot('componente')
        print("intent: ", tracker.latest_message.get("intent").get("name"))
        print(tracker.latest_message.get("text"))
        if seccion is None:
            seccion = tracker.get_slot('tipo_seccion')
        if seccion:
            return [FollowupAction("action_capturar_tipo_seccion"), SlotSet("creando_seccion", True)]
        else:
            return [FollowupAction("action_preguntar_nombre_pagina"), SlotSet("creando_pagina", True)]

    def skip_tuto_verification(self) -> bool:
        return False

class ActionPreguntarNombrePagina(BaseAction):

    def name(self):
        return "action_preguntar_nombre_pagina"

    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="¿Como queres que se llame tu pagina? Por favor indica su nombre en el siguiente formato:")
        dispatcher.utter_message(text="&&nombre-pagina&&")
        return [SlotSet("creando_pagina", True), SlotSet("pregunta_nombre", True)]

class ActionCrearPagina(BaseAction):

    def name(self) -> Text:
        return "action_crear_pagina"

    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        global creando_pagina, slots_crear_pagina, dbm, pgm
        print("creando_pagina: ", creando_pagina)
        last_user_message = tracker.latest_message.get("text")
        last_message_intent = tracker.latest_message.get('intent').get('name')
        #if not 'nombre_pagina' in last_message_intent:
        if not "&&" in last_user_message:
            dispatcher.utter_message(text="Entendido, si mas tarde deseas retomar la creacion de tu pagina puedes pedirmelo.")
            return [SlotSet("creando_pagina", False), SlotSet("pregunta_nombre", False)]
        print("slot creando: ", tracker.get_slot("creando_pagina"))
        print("page_name: ", page_name)

        if tracker.get_slot("creando_pagina"):
            if not page_name:
                dispatcher.utter_message(
                    text="Repetime como queres que se llame tu página. Te recuerdo que el formato es: &&nombre-pagina&&")
                return [SlotSet("creando_pagina", True), SlotSet("pregunta_nombre", True)]
            else:
                if creando_pagina:
                    print("entro a creando pagina")
                    page = pgm.get_page(user_id, page_name)
                    message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page.get_page_address()
                    dispatcher.utter_message(text=message)
                    #message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
                    #dispatcher.utter_message(text=message)
                    creando_pagina = False
                    return [SlotSet("creando_pagina", False), SlotSet("pregunta_nombre", False)]
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
                    return [SlotSet("creando_pagina", True), SlotSet("pregunta_nombre", True)]
        else:
            return []
class ActionEjecutarDev(Action):

    def name(self) -> Text:
        return "action_ejecutar_dev"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global creando_pagina, pgm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()

        #Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
        pgm.run_dev(user_id, page_name)

        page = pgm.get_page(user_id, page_name)
        message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page.get_page_address()
        dispatcher.utter_message(text=message)

        #message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
        #dispatcher.utter_message(text=message)
        return [SlotSet("creando_pagina", False), SlotSet("pregunta_nombre", False)]

class ActionEjecutarPagina(BaseAction):

    def name(self) -> Text:
        return "action_ejecutar_pagina"

    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        global dbm, pgm
        if pgm.is_alive(user_id, page_name):
        # La pagina esta viva
            page_obj = pgm.get_page(user_id, page_name)
            if page_obj.is_running():
            # Verificar si la pagina está ejecutando
                dispatcher.utter_message(text="Podes acceder a tu página en el siguiente link: " + page_obj.get_page_address())
                #dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
                return []
            elif page_obj.is_running_dev():
            # Se esta ejecutando en modo dev
                pgm.stop_page(user_id, page_name)
                #pgm.stop_tunnel(user_id, page_name)
        else:
        # La pagina no vive en PageManager
            page_obj = pgm.add_page(user_id, page_name)
        #Verificar si esta compilada
        if not dbm.was_compiled(user_id, page_name):
            print("(" + threading.current_thread().getName() + ") " + "----------------pagina no compilada")
            pgm.build_project(user_id, page_name)
            dbm.set_compilation_date(user_id, page_name)
        else:
            print("(" + threading.current_thread().getName() + ") " + "----------------pagina ya compilada")

        # Inicia la ejecución del proyecto en modo desarrollo en un nuevo hilo
        pgm.run_project(user_id, page_name)
        print("(" + threading.current_thread().getName() + ") " + "------------PAGINA COMPILADA")

        page_address = page_obj.get_page_address()
        print("(" + threading.current_thread().getName() + ") " + "------------page_address: ", page_address)
        dispatcher.utter_message(text="Podes acceder a tu página en el siguiente link: " + page_address)
        #dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
        return [SlotSet("pregunta_ejecucion", False)]

    def skip_tuto_verification(self) -> bool:
        return False

    def skip_page_verification(self) -> bool:
        return False

    class ActionDetenerPagina(BaseAction):

        def name(self) -> Text:
            return "action_detener_pagina"

        def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any],
                          user_id: Text,
                          page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
            global pgm
            last_message_entities = tracker.get_latest_entity_values("text")
            print("(" + threading.current_thread().getName() + ") " + "--------last_message_entities: ", last_message_entities)
            if "todas" in tracker.latest_message.get("text"):
            # Quiere detener todas
                for pag in pgm.get_user_running_pages(user_id):
                    pgm.stop_page(user_id, pag.get_name())
                    #pgm.stop_tunnel(user_id, pag.get_name())
                    pgmpgm.pop_page(user_id, pag.get_name())
                    dispatcher.utter_message(text="La pagina " + pag.get_name() + " fue detenida con éxito.")
                print("(" + threading.current_thread().getName() + ") " + "------------PAGINAS DETENIDA CON EXITO------------")
            else:
            #No especifico cual quiere detener pero hay slot de contexto
                if page_name:
                    pgm.stop_page(user_id, page_name)
                    #pgm.stop_tunnel(user_id, page_name)
                    pgm.pop_page(user_id, page_name)
                    print("(" + threading.current_thread().getName() + ") " + "------------PAGINA DETENIDA CON EXITO------------")
                    dispatcher.utter_message(text="Tu pagina fue apagada con exito.")
            return [SlotSet("pregunta_detencion", False)]

        def skip_tuto_verification(self) -> bool:
            return False

        def skip_page_verification(self) -> bool:
            return False

class ActionCapturarEdicion(BaseAction):

    def name(self) -> Text:
        return "action_capturar_edicion"

    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        global dbm
        if pgm.is_alive(user_id, page_name):
        # La pagina esta viva
            page_obj = pgm.get_page(user_id, page_name)
            if page_obj.is_running():
                pgm.switch_dev(user_id, page_name)
                dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address())
            #dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
            if not page_obj.is_running_dev():
                pgm.run_dev(user_id, page_name)
                dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address())
                #dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
        else:
        # La pagina no está viva, hay que recuperar sus datos de la db
            page_obj = pgm.add_page(user_id, page_name)
            pgm.run_dev(user_id, page_name)
            dispatcher.utter_message(text="Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address())
            #dispatcher.utter_message(text="Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password())
        componente = tracker.get_slot('componente')
        print("(" + threading.current_thread().getName() + ") " + "--------componente: ", componente)
        if componente:
        # Hay componente a modificar
            if componente.lower() == "color":
                return [FollowupAction("action_preguntar_color"), SlotSet("cambio_logo", True), SlotSet("pregunta_componente", False),
                        SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
            if componente.lower() == "logo":
                dispatcher.utter_message("Podes enviarme una imagen con el logo de tu página para el encabezado. Te recomiendo que la envíes como archivo para que esta conserve su calidad original.")
                return [SlotSet("cambio_logo", True)]
            elif componente.lower() == "footer":
                return [FollowupAction("action_preguntar_mail_footer"), SlotSet("pregunta_componente", False),
                        SlotSet("pregunta_nombre", False), SlotSet("pregunta_edicion", False)]
            elif componente.lower() == "seccion":
            # Va a editar una seccion
                tipo_seccion = tracker.get_slot('tipo_seccion')
                print("(" + threading.current_thread().getName() + ") " + "--------tipo_seccion: ", tipo_seccion)
                nombre_seccion = tracker.get_slot('nombre_informativa')
                if nombre_seccion is not None:
                    nombre_seccion = nombre_seccion[2:len(nombre_seccion) - 2].strip()
                print("(" + threading.current_thread().getName() + ") " + "--------nombre_informativa: ", nombre_seccion)
                secciones = page_obj.get_sections_name()
                print(secciones)
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
                            buttons = []
                            for seccion in secciones:
                                buttons.append({"payload": "$$" + str(seccion) + "$$", "title": seccion})
                            dispatcher.utter_message(text=str(nombre_seccion) + " no es un tipo de seccion válido. Te recuerdo que las secciones a modificar en tu página son:", buttons=buttons, button_type="vertical")
                            return [SlotSet("pregunta_componente", False), SlotSet("pregunta_seccion", True)]
                    else:
                        buttons = []
                        for seccion in secciones:
                            buttons.append({"payload": "$$" + str(seccion) + "$$", "title": seccion})
                        dispatcher.utter_message(text="¿Sobre qué sección te gustaría operar?. Te recuerdo que las secciones de tu página son:", buttons=buttons, button_type="vertical")
                        return [SlotSet("pregunta_componente", True), SlotSet("pregunta_seccion", True)]
                else:
                # La pagina no tiene secciones
                    dispatcher.utter_message(text="La pagina " + page_doc.name + " no cuenta con ninguna sección, por lo que antes deberás crear una.")
                    return [FollowupAction("action_capturar_tipo_seccion")]
        else:
        # No hay componente a modificar
            buttons = [{"payload": "quiero cambiar el color", "title": "Color"}, {"payload": "quiero cambiar el logo", "title": "Logo"}]
            secciones = page_obj.get_sections_name()
            sects = "("
            for seccion in secciones:
                sects +=str(seccion) + ", "
            sects = sects[:len(sects) - 2] + ")"
            buttons.append({"payload": "quiero modificar una seccion", "title": "Sección " + sects})
            buttons.append({"payload": "quiero cambiar el color", "title": "Footer"})
            message = "¿Qué componente de tu página te gustaría modificar? Te recuerdo que sus componentes son:"
            dispatcher.utter_message(text=message, buttons=buttons, button_type="vertical")
            return [SlotSet("pregunta_componente", True)]


    def skip_tuto_verification(self) -> bool:
        return False

    def skip_page_verification(self) -> bool:
        return False

class ActionRecibirImagen(Action):
    def name(self) -> Text:
        return "action_recibir_imagen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm, tbm, rg
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        print("(" + threading.current_thread().getName() + ") " + "--------creando_seccion_informativa ", tracker.get_slot("creando_seccion_informativa"))
        print("(" + threading.current_thread().getName() + ") " + "--------pregunta_otra_imagen_seccion_informativa ", tracker.get_slot("pregunta_otra_imagen_seccion_informativa"))
        print("(" + threading.current_thread().getName() + ") " + "--------last_message_intent: ", tracker.latest_message.get('intent').get('name'))
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        page_path = pgm.get_page_path(user_id, page_name)

        # Verifica si el último mensaje contiene una imagen
        last_user_message = str(tracker.latest_message.get('text'))
        if not "photo" in last_user_message:
        # El usuario no envió una imagen
            if tracker.get_slot("cambio_logo"):
                dispatcher.utter_message(text="Perfecto, mantendremos el logo por defecto.")
                return []
            elif tracker.get_slot("creando_seccion_informativa"):
                return [SlotSet("pregunta_otra_imagen_seccion_informativa", False)]
            elif tracker.get_slot("editando_seccion_informativa"):
                return [SlotSet("pregunta_otra_imagen_seccion_informativa", False)]
            elif tracker.get_slot("agregando_productos"):
                return [SlotSet("agregando_productos", False), SlotSet("pregunta_carga", False)]
            else:
                return []

        if "document" in last_user_message:
        # El usuario envió la imagen como documento
            file = tracker.latest_message['metadata']['message']['document']
        else:
        # El usuario envió la imagen como foto
            file = tracker.latest_message['metadata']['message']['photo'][1]
        error = self.download_image(user_id, page_name, page_path, file, tracker, dispatcher)

        if not error:
            dispatcher.utter_message(text="Imagen recibida con éxito.")
        else:
            dispatcher.utter_message(text="No se pudo procesar la imagen.")

        if tracker.get_slot("cambio_logo") is True:
            dispatcher.utter_message("Podes ver el nuevo logo en tu página.")
            return [SlotSet("cambio_logo", not error)]
        elif tracker.get_slot("creando_seccion_informativa") is True:
            dispatcher.utter_message(text="¿Queres agregar otra imagen?")
            return [SlotSet("pregunta_otra_imagen_seccion_informativa", True)]
        elif tracker.get_slot("agregando_productos") is True:
            dispatcher.utter_message(text="¿Queres cargar otro producto?")
            return [SlotSet("pregunta_carga", True), SlotSet("pide_img_prod", False)]
        return []

    def download_image(self, user_id, page_name, page_path, file, tracker: Tracker, dispatcher: CollectingDispatcher) -> bool:
        global tbm, dbm
        error = False
        image_id = file["file_id"]
        if not image_id:
            error = True
        else:
            if tracker.get_slot("cambio_logo"):
                utils.go_to_main_dir()
                tbm.download_image(page_path=page_path, subdir="components", image_id=image_id, image_name="logo.png")
                rg.set_favicon(page_path)
            elif tracker.get_slot("creando_seccion_informativa"):
                utils.go_to_main_dir()
                tbm.download_image(page_path=page_path, subdir="sect_inf_images", image_id=image_id, image_name=(file["file_unique_id"] + ".png"))
            elif tracker.get_slot("agregando_productos"):
                # Descargar imagen
                image_url = tbm.get_image_url(image_id=image_id)
                print(tracker.get_slot("id_producto"))
                dbm.set_product_multimedia(user_id, page_name, tracker.get_slot("id_producto"), image_url)
        return error

class ActionPreguntarColor(Action):
    def name(self) -> Text:
        return "action_preguntar_color"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="¿Querés modificar el color principal de tu página? En ese caso necesito que me proveas su codigo hexadecimal. Podes seleccionar tu color y copiar su codigo en el siguiente link: https://g.co/kgs/FMBcG8K")
        return [SlotSet("pregunta_color", True), FollowupAction("action_listen")]


class ActionCapturarColor(Action):
    def name(self) -> Text:
        return "action_capturar_color"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global pgm, rg
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        color = tracker.get_slot('color')

        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        rg.set_colors(pgm.get_page_path(tracker.sender_id, page_name), color)
        dispatcher.utter_message("Podes ver el nuevo color en tu página.")
        return [SlotSet("componente", None), SlotSet("pregunta_color", False), SlotSet("cambio_color", False)]


class ActionPreguntarMailFooter(Action):
    def name(self) -> Text:
        return "action_preguntar_mail_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="¿Queres cambiar tu e-mail en el footer?")
        return [SlotSet("creando_footer", True), FollowupAction("action_listen")]

class ActionGuardarMailFooter(Action):
    def name(self) -> Text:
        return "action_guardar_mail_footer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        print("(" + threading.current_thread().getName() + ") ", tracker.slots.items())
        last_message_intent = tracker.latest_message.get('intent').get('name')
        print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        if 'decir_mail' in last_message_intent:
        #El usuario proporciono el mail
            mail = tracker.get_slot('mail')
            print("(" + threading.current_thread().getName() + ") " + "------------mail: ", mail)
            #Guardar el mail en la pagina
            dbm.set_page_mail(tracker.sender_id, page_name, mail)
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
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        last_message_intent = tracker.latest_message.get('intent').get('name')
        print("(" + threading.current_thread().getName() + ") " + "--------last message intent: ", last_message_intent)
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        if 'decir_ubicacion' in last_message_intent:
        #El usuario proporciono su ubicacion
            ubicacion = tracker.get_slot("ubicacion")
            print("(" + threading.current_thread().getName() + ") " + "------------ubicacion: ", ubicacion)
            #Guardar la ubicacion en la pagina
            dbm.set_page_location(tracker.sender_id, page_name, ubicacion)
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
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        page_path = pgm.get_page_path(user_id, page_name)
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
        rg.generarFooter(page_path, mail, ubicacion)
        print("-------------FOOTER MODIFICADO-------------")
        dispatcher.utter_message(text="Podes ver los cambios que realizamos en el footer")
        return [SlotSet("creando_footer", False), SlotSet("componente", None)]

# SECCIONES

## CREAR
class ActionCapturarTipoSeccion(BaseAction):
    def name(self) -> Text:
        return "action_capturar_tipo_seccion"

    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        global dbm, pgm, creando_ecommerce
        print("(" + threading.current_thread().getName() + ") " + "--------page_name: ", page_name)
        print("(" + threading.current_thread().getName() + ") " + "--------page_doc.name: ", page_doc.name)
        if pgm.is_alive(user_id, page_name):
            page_obj = pgm.get_page(tracker.sender_id, page_doc.name)
        else:
            page_obj = pgm.add_page(tracker.sender_id, page_doc.name)
        print("(" + threading.current_thread().getName() + ") " + "--------page_obj.name: ", page_obj.get_name())
        if not tracker.get_slot('tipo_seccion') == "e-commerce":
            if not page_obj.is_running_dev():
                pgm.run_dev(user_id, page_name)
                message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address()
                dispatcher.utter_message(text=message)
            elif page_obj.is_running():
                pgm.switch_dev(tracker.sender_id, page_doc.name)
                message = "Tu pagina se encuentra en modo edición. Podrás visualizar los cambios que realices en: " + page_obj.get_page_address()
                dispatcher.utter_message(text=message)
            #message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
            #dispatcher.utter_message(text=message)
        tipo_seccion = tracker.get_slot('tipo_seccion')
        print("(" + threading.current_thread().getName() + ") " + "--------tipo_seccion: ", tipo_seccion)
        if tipo_seccion:
            # Hay tipo seccion
            if "e-commerce" in tipo_seccion.lower():
                if creando_ecommerce:
                    creando_ecommerce = False
                    if not page_obj.is_running_dev():
                        pgm.run_dev(user_id, page_name)
                        message = "Tu pagina se encuentra en modo edición. Podrás visualizar la nueva sección en: " + page.get_page_address()
                        dispatcher.utter_message(text=message)
                        #message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
                        #dispatcher.utter_message(text=message)
                    else:
                        dispatcher.utter_message(text="Podes ver la nueva sección en tu página.")
                    return self.clear_slots(tracker, domain, slots_to_save=["page_name"])
                    #return [SlotSet("pregunta_seccion", False), SlotSet("creando_seccion", False), SlotSet("componente", None)]
                else:
                    dispatcher.utter_message(text="Aguarda un momento mientras se crea la sección e-commerce en tu página.")
                    return [FollowupAction("action_crear_ecommerce")]
            elif "informativa" in tipo_seccion.lower():
                return [FollowupAction("action_crear_informativa_1"), SlotSet("pregunta_edicion", False)]
            else:
                message = str(tipo_seccion) + " no es un tipo de seccion válido. Te recuerdo que las secciones a crear son: "
                buttons = [{"payload": "el tipo de la seccion es e-commerce", "title": "E-Commerce"}, {"payload": "el tipo de la seccion es informativa", "title": "Informativa"}]
                dispatcher.utter_message(text=message, buttons=buttons, button_type="vertical")
                return [SlotSet("pregunta_seccion", True), SlotSet("pregunta_nombre", True), SlotSet("componente", "seccion")]
        else:
            # No hay tipo seccion
            message = "¿Que tipo de sección te gustaría crear? Te recuerdo que las posibles secciones son:"
            buttons = [{"payload": "el tipo de la seccion es e-commerce", "title": "E-Commerce"}, {"payload": "el tipo de la seccion es informativa", "title": "Informativa"}]
            dispatcher.utter_message(text=message, buttons=buttons, button_type="vertical")
            for slot in tracker.slots.keys():
                print(slot + " : " + str(tracker.slots[slot]))
            return self.clear_slots(tracker, domain, slots_to_true=["creando_seccion", "pregunta_seccion"], slots_to_save=["componente", "page_name"])

    def skip_tuto_verification(self) -> bool:
        return False

    def skip_page_verification(self) -> bool:
        return False

### E-COMMERCE

class ActionCrearEcommerce(BaseAction):

    def name(self):
        return "action_crear_ecommerce"

    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        global dbm, pgm, creando_ecommerce
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        page = pgm.get_page(user_id, page_name)
        seccion = page.get_section("e-commerce")
        if seccion:
            dispatcher.utter_message(text="Tu página ya tiene una sección de e-commerce.")
        else:
            creando_ecommerce = True
            page.add_section(EcommerceSection())
            pgm.add_ecommerce(user_id, page_name)
            if not page.is_running_dev():
                pgm.run_dev(user_id, page_name)
                message = "Tu pagina se encuentra en modo edición. Podrás visualizar la nueva sección en: " + page.get_page_address()
                dispatcher.utter_message(text=message)
                #message = "Si la pagina te solicita una contraseña ingresa: " + pgm.get_tunnel_password()
                #dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Podes ver la nueva sección en tu página.")
            dbm.add_ecomm_section(user_id, page_name)
        return self.clear_slots(tracker, domain, slots_to_save=["page_name"])
        #return [SlotSet("pregunta_seccion", False), SlotSet("creando_seccion", False), SlotSet("componente", None)]

    def skip_page_verification(self) -> bool:
        return False

#### AGREGAR PRODUCTOS

class ActionPedirProductos(BaseAction):

    def name(self) -> Text:
        return "action_pedir_productos"

    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        global dbm, tbm
        if page_doc.has_ecomm_section:
        # Tiene sección ecommerce
            message = "Podes agregar los productos de a uno o cargar múltiples productos en un archivo de datos y enviármelo. Si optas por la carga mediante archivo, completa la siguiente planilla agregando los datos en una nueva fila. En los campos \"multimedia\" coloca el link a las imágenes o videos del producto"
            dispatcher.utter_message(text=message)
            utils.go_to_main_dir()
            tbm.send_file_to_user(user_id, CONSTANTS.TEMPLATE_PRODUCTOS_DIR)
            dispatcher.utter_message(text="Si vas a cargar los productos de a uno voy a necesitar los siguientes datos:")
            dispatcher.utter_message(text="SKU:\nCantidad:\nTitulo:\nDescripción:\nPrecio:")
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

    def skip_tuto_verification(self) -> bool:
        return False

    def skip_page_verification(self) -> bool:
        return False

class ActionCapturarProductoCargado(Action):

    def name(self) -> Text:
        return "action_capturar_producto_cargado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, tbm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        # Verifica si el último mensaje contiene una imagen
        latest_message = tracker.latest_message
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        if 'document' in latest_message['metadata']['message']:
            error = False
            documento = latest_message['metadata']['message']['document']
            file_id = documento['file_id']
            if not documento:
                error = True
            else:
                file = tbm.get_file(file_id)
                file_bytes = BytesIO()
                file.download(out=file_bytes)
                file_bytes.seek(0)
                df = pd.read_excel(file_bytes, engine='openpyxl')
                for producto in df.itertuples(index=True, name='Pandas'):
                    if pd.isna(producto.Cantidad):
                        break
                    else:
                        dbm.add_product(
                            user_id=tracker.sender_id,
                            page_name=page_name,
                            sku=int(producto.SKU),
                            cant=int(producto.Cantidad),
                            title=producto.Titulo,
                            desc=producto.Descripcion,
                            precio=float(producto.Precio)
                        )

                        # Verifica si Imagen_principal no es nan
                        if pd.notna(producto.Imagen_principal):
                            dbm.set_product_multimedia(
                                tracker.sender_id,
                                page_name,
                                int(producto.SKU),
                                str(producto.Imagen_principal)
                            )
                        message = "El producto " + producto.Titulo + " se guardó correctamente con el identificador: " + str(int(producto.SKU))
                        dispatcher.utter_message(text=message)
                dispatcher.utter_message(text="Ha finalizado la carga de productos. ¿Puedo ayudarte con algo más?")
                return [FollowupAction("action_listen"), SlotSet("agregando_productos", False), SlotSet("pregunta_carga", False)]
            if error:
                dispatcher.utter_message(text="No se pudo recibir el archivo. Por favor envíalo nuevamente.")
                return [SlotSet("agregando_productos", True), SlotSet("pregunta_carga", True)]
        else:
            last_message = str(tracker.latest_message.get('text'))
            print("(" + threading.current_thread().getName() + ") " + "--------last_message: \n", last_message)
            sku = tracker.get_slot("sku_prod")
            print("(" + threading.current_thread().getName() + ") " + "--------sku: \n", sku)
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
            dbm.add_product(user_id=tracker.sender_id, page_name=page_name, sku=int(sku), cant=int(cant), title=titulo, desc=desc, precio=float(precio))
            message = "El producto " + titulo + " se guardó correctamente con el identificador: " + str(int(sku))
            dispatcher.utter_message(text=message)
            dispatcher.utter_message(text="Si lo deseas podes enviarme alguna imagen sobre él.")
            return [SlotSet("pide_img_prod", True), SlotSet("id_producto", sku)]


### INFORMATIVA

class ActionCrearInformativa1(Action):

    def name(self) -> Text:
        return "action_crear_informativa_1"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="¿Que nombre llevará la sección? Por favor utiliza el siguiente formato:")
        dispatcher.utter_message(text="$$nombre seccion$$")
        return [SlotSet("creando_seccion_informativa", True), SlotSet("pregunta_nombre_informativa", True)]


class ActionCrearInformativa2(Action):

    def name(self) -> Text:
        return "action_crear_informativa_2"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global pgm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        print("(" + threading.current_thread().getName() + ") " + "--------page_name: ", page_name)
        page = pgm.get_page(tracker.sender_id, page_name)
        nombre_seccion = tracker.get_slot('nombre_informativa')
        if nombre_seccion is not None:
            nombre_seccion = nombre_seccion[2:len(nombre_seccion) - 2].strip()
            dispatcher.utter_message(text="Nombre de sección guardado.")
        else:
            nombre_seccion = "Informativa"
        inf_section = InformativeSection(nombre_seccion)
        print("titulo seccion creada: ", inf_section.get_title())
        page.add_section(inf_section)
        dispatcher.utter_message(text="Proporcioname el texto informativo. Puedes enviarme un archivo en formato MarkDown (.md) o simplemente escribir en este chat. Si vas a escribir en el chat, por favor respeta el siguiente formato:")
        dispatcher.utter_message(text="%%\nTexto\n%%")
        return [SlotSet("componente", "seccion"), SlotSet("creando_seccion_informativa", True), SlotSet("pide_text_informativa", True), SlotSet("pregunta_nombre_informativa", False), SlotSet("nombre_informativa", nombre_seccion), SlotSet("pagina_modificando", tracker.get_slot('page_name'))]

class ActionCrearInformativa3(Action):

    def name(self) -> Text:
        return "action_crear_informativa_3"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm, rg
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot('pagina_modificando')
        if page_name is not None:
            if "&&" in page_name:
                page_name = page_name[2:len(page_name) - 2].strip()
        text = self.handle_text(tracker)
        nombre_seccion = tracker.get_slot('nombre_informativa')
        if nombre_seccion is None:
            nombre_seccion = "Informacion"
        print("nombre_pagina: ", page_name)
        page = pgm.get_page(user_id, page_name)
        print("nombre_pagina: ", page.get_name())
        print("nombre_informativa: ", nombre_seccion)
        print(len(nombre_seccion))
        inf_section = page.get_section(nombre_seccion)
        inf_section.set_text(text)
        dbm.add_inf_section(user_id, page_name, inf_section)
        page_path = pgm.get_page_path(user_id, page_name)
        if page.get_cant_sections() > 0:
            rg.remove_section(page_path, "Template")
        rg.agregarSectionInformativa(page_path, nombre_seccion, text)
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("creando_seccion_informativa", False), SlotSet("pide_text_informativa", False), SlotSet("pregunta_seccion", False),
                SlotSet("creando_seccion", False), SlotSet("componente", None), SlotSet("nombre_informativa", None), SlotSet("tipo_seccion", None)]

    def handle_text(self, tracker: Tracker) -> Text:
        global tbm
        last_user_message = str(tracker.latest_message.get('text'))
        if last_user_message == "text.md":
            file_id = tracker.latest_message['metadata']['message']['document']['file_id']
            file = tbm.get_file(file_id)
            file_content = file.download_as_bytearray()
            file_text = file_content.decode('utf-8')  # Decodificar el contenido a 'utf-8'
            return f"""{file_text}"""
        else:
            return last_user_message[2:len(last_user_message) - 2].strip()

## EDITAR

### INFORMATIVA

class ActionModificarInformativa1(Action):

    def name(self) -> Text:
        return "action_modificar_informativa_1"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="¿Cuál es el nuevo contenido de la sección? Puedes enviarme un archivo en formato MarkDown (.md) o simplemente escribir en este chat. Si vas a escribir en el chat, por favor respeta el siguiente formato:")
        dispatcher.utter_message(text="%%\nTexto\n%%")
        return [SlotSet("editando_seccion_informativa", True), SlotSet("pide_text_informativa", True)]


class ActionModificarInformativa2(Action):

    def name(self) -> Text:
        return "action_modificar_informativa_2"


    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm, rg
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        user_id = tracker.sender_id
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        last_user_message = str(tracker.latest_message.get('text'))
        text = self.handle_text(tracker)
        page = pgm.get_page(tracker.sender_id, page_name)
        nombre_seccion = tracker.get_slot('nombre_informativa')
        if nombre_seccion is not None:
            nombre_seccion = nombre_seccion[2:len(nombre_seccion) - 2].strip()
        else:
            nombre_seccion = tracker.get_slot("nombre_seccion_editando")
        inf_section = page.get_section(nombre_seccion)
        inf_section.set_text(text)
        dispatcher.utter_message(text="Texto informativo guardado.")
        dbm.updt_inf_section(user_id, page_name, nombre_seccion, text)
        utils.go_to_main_dir()
        rg.remove_section(pgm.get_page_path(user_id, page_name), tracker.get_slot("nombre_seccion_editando"), False)
        rg.agregarSectionInformativa(pgm.get_page_path(user_id, page_name), nombre_seccion, text, is_update=True)
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("editando_seccion_informativa", False), SlotSet("pide_text_informativa", False), SlotSet("nombre_informativa", None), SlotSet("nombre_seccion_editando", None)]

    def handle_text(self, tracker: Tracker) -> Text:
        global tbm
        last_user_message = str(tracker.latest_message.get('text'))
        if last_user_message == "text.md":
            file_id = tracker.latest_message['metadata']['message']['document']['file_id']
            file = tbm.get_file(file_id)
            file_content = file.download_as_bytearray()
            file_text = file_content.decode('utf-8')  # Decodificar el contenido a 'utf-8'
            return f"""{file_text}"""
        else:
            return last_user_message[2:len(last_user_message) - 2].strip()


class ActionModificarInformativa4(Action):

    def name(self) -> Text:
        return "action_modificar_informativa_4"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm, pgm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        page_name = tracker.get_slot('page_name')
        if page_name is not None:
            page_name = page_name[2:len(page_name) - 2].strip()
        page = pgm.get_page(tracker.sender_id, page_name)
        nombre_seccion = tracker.get_slot('nombre_informativa')
        if nombre_seccion is not None:
            nombre_seccion = nombre_seccion[2:len(nombre_seccion) - 2].strip()
        else:
            nombre_seccion = tracker.get_slot("nombre_seccion_editando")
        inf_section = page.get_section(nombre_seccion)
        dbm.updt_inf_section(tracker.sender_id, page_name, tracker.get_slot("nombre_seccion_editando"),  inf_section)
        dispatcher.utter_message(text="Podrás ver la nueva sección en tu página")
        return [SlotSet("editando_seccion_informativa", False)]

# Saludo Actions
class ActionSaludoTelegram(Action):

    def name(self) -> Text:
        return "action_saludo_telegram"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
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
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
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
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        pages = dbm.get_user_pages(tracker.sender_id)
        if pages:
            message = "Tus paginas son: \n"
            for page in pages:
                message += page.name + "\n"
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text="Todavía no creaste ninguna página.")
        return []

# TUTORIAL

class ActionCapturarTutorial(Action):

    def name(self) -> Text:
        return "action_capturar_tutorial"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
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
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Antes que nada debes saber que nuestras páginas se conforman por lo que denominamos componentes. A continuación te explicaré cada uno de ellos.")
        dispatcher.utter_message(text="El primero de ellos es el color, el cual puedes modificar con tan solo pedirmelo.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_1_confirmacion", True)]


class ActionPregunta1Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_1_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Enviandome un mensaje como \"Quiero cambiar el color de mi pagina\" te solicitaré el valor en formato hexadecimal del color que desees y se aplicará a tu página.")
        dispatcher.utter_message(text="En este video se aprecia el cambio de color tras enviarme el color \"#e62c0b\".", attachment="https://youtu.be/v7xBYZHmAHs")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_1_confirmacion", False), SlotSet("pregunta_1_repetir_confirmacion", True)]


class ActionPregunta2(Action):

    def name(self) -> Text:
        return "action_pregunta_2"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="El siguiente componente es el logo. Este debe ser una imagen en formato \".png\". Puedes pedirme que modifique el logo de tu página cuando lo desees.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_2_confirmacion", True), SlotSet("pregunta_2_repetir_confirmacion", False)]


class ActionPregunta2Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_2_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Enviandome un mensaje como \"Quiero cambiar el logo de mi pagina\" te solicitaré que me envíes una imagen para utilizar como el nuevo logo.")
        dispatcher.utter_message(text="En este gif se aprecia el cambio de logo tras enviar una imagen como documento.")
        dispatcher.utter_message(attachment="https://youtu.be/2ERmPt_Qgc4")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_2_confirmacion", False), SlotSet("pregunta_2_repetir_confirmacion", True)]

class ActionPregunta3(Action):

    def name(self) -> Text:
        return "action_pregunta_3"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="El siguiente componente de nuestras páginas es el cuerpo, el cual dividimos según secciones de dos tipos: e-commerce e informativa.")
        dispatcher.utter_message(text="Seccion e-commerce:\nEsta sección te permite montar una tienda en tu página, cargar productos y que los usuarios puedan comprarlos. Cada página puede tener una única sección de e-commerce")
        dispatcher.utter_message(text="Seccion informativa:\nEsta sección te permite incluir información sobre tu página o empresa. Una página puede tener múltiples secciones informativas con distintos nombres.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_2_confirmacion", False), SlotSet("pregunta_2_repetir_confirmacion", False), SlotSet("pregunta_3_confirmacion", True)]


class ActionPregunta3Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_3_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="El cuerpo de nuestras páginas está compuesto por secciones de tipo informativas o de e-commerce. Avanzando en el tutorial te explicaré cómo crear y modificar estas secciones.")
        dispatcher.utter_message(text="Así es como se ve una sección de tipo informativa")
        dispatcher.utter_message(image="https://imgur.com/a/pcPbh0D")
        dispatcher.utter_message(text="Y así es como se ve una sección e-commerce")
        dispatcher.utter_message(image="https://imgur.com/a/jynPJTW")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_3_confirmacion", False), SlotSet("pregunta_3_repetir_confirmacion", True)]

class ActionPregunta4(Action):

    def name(self) -> Text:
        return "action_pregunta_4"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Finalmente llegamos al footer, que es el componente de la página encontrado al final de la misma.")
        dispatcher.utter_message(text="Este se compone por el informacion del contacto, licencias y más.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_3_confirmacion", False), SlotSet("pregunta_3_repetir_confirmacion", False), SlotSet("pregunta_4_confirmacion", True)]


class ActionPregunta4Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_4_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="El footer es el pie de página de tu web y en él podes modificar los datos de contacto de tu página o empresa.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_4_confirmacion", False), SlotSet("pregunta_4_repetir_confirmacion", True)]

class ActionPregunta5(Action):

    def name(self) -> Text:
        return "action_pregunta_5"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Ya repasamos cuales son los componentes de una página, por lo que el siguiente paso es aprender a crear una página.")
        dispatcher.utter_message(text="Para ello sólo es necesario un mensaje como \"Quiero crear una pagina\" y yo te preguntaré cuál será su nombre.")
        return [SlotSet("pregunta_4_confirmacion", False), SlotSet("pregunta_4_repetir_confirmacion", False), SlotSet("pregunta_5_confirmacion", True)]

class ActionPregunta5Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_5_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Si me envias un mensaje como \"Quiero crear una pagina\" o \"Quiero una nueva pagina\" iniciaremos el proceso de creación de tu página web. Deberás proporcionarme un nombre, el cuál siempre que lo utilices deberás encerrar entre \"&&\".")
        dispatcher.utter_message(text="Por ejemplo, un nombre válido para una página puede ser \"DesignLabel\". Sin embargo, para que yo pueda interpretarlo inequivocamente necesito que lo escribas como \"&&DesignLabel&&\"")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_5_confirmacion", False), SlotSet("pregunta_5_repetir_confirmacion", True)]

class ActionPregunta6(Action):

    def name(self) -> Text:
        return "action_pregunta_6"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Con tu página ya creada, el siguiente paso es crear una sección. Puedes iniciar este proceso con un mensaje como \"Quiero crear una seccion\".")
        dispatcher.utter_message(text="Luego podrás decidir si la nueva sección será de tipo informativa o e-commerce.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_5_confirmacion", False), SlotSet("pregunta_5_repetir_confirmacion", False), SlotSet("pregunta_6_confirmacion", True)]

class ActionPregunta6Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_6_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Si me envias un mensaje como \"Quiero crear una seccion\" o \"Quiero una nueva seccion\" iniciaremos el proceso de creación de una sección.")
        dispatcher.utter_message(text="De esta manera se crea una sección informativa. Notarás que debes proporcionar un nombre, el cual deberás encerrar entre \"$$\".")
        dispatcher.utter_message(attachment="https://youtu.be/-GVppQu9jZE")
        dispatcher.utter_message(text="Y así es como se crea una sección e-commerce.")
        dispatcher.utter_message(attachment="https://youtu.be/OO7hLl0ElgQ")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_6_confirmacion", False), SlotSet("pregunta_6_repetir_confirmacion", True)]

class ActionPregunta7(Action):

    def name(self) -> Text:
        return "action_pregunta_7"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Ya sabes como crear una sección, ahora te mostraré como modificarlas, comenzando por la modificación de una sección informativa.")
        dispatcher.utter_message(text="Para ello deberás enviarme un mensaje como \"Quiero modificar una seccion\" o \"Quiero modificar la seccion $$¿Como comprar?$$\". Luego podrás proporcionarme el nuevo contenido de la sección en particular.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_6_confirmacion", False), SlotSet("pregunta_6_repetir_confirmacion", False), SlotSet("pregunta_7_confirmacion", True)]

class ActionPregunta7Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_7_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="En este video podrás ver el proceso de edición de una sección informativa. Solo necesitas especificarme cuál es la sección a modificar y proporcionarme su nuevo contenido.")
        dispatcher.utter_message(attachment="https://youtu.be/iY-MTk2HdNo")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_7_confirmacion", False), SlotSet("pregunta_7_repetir_confirmacion", True)]

class ActionPregunta8(Action):

    def name(self) -> Text:
        return "action_pregunta_8"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="En el caso de las secciones e-commerce, estas pueden modificarse cargando productos. Para ello deberás enviarme un mensaje como \"Quiero cargar productos\" y yo te indicaré como avanzar.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_7_confirmacion", False), SlotSet("pregunta_7_repetir_confirmacion", False), SlotSet("pregunta_8_confirmacion", True)]

class ActionPregunta8Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_8_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Si quieres cargar productos en la sección e-commerce de tu página podes hacerlo tal como se muestra en este video.")
        dispatcher.utter_message(attachment="https://youtu.be/QoGadncgAxU") #PONER GIF CARGA PRODUCTOS
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_8_confirmacion", False), SlotSet("pregunta_8_repetir_confirmacion", True)]

class ActionPregunta9(Action):

    def name(self) -> Text:
        return "action_pregunta_9"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Para este punto solo queda guardar los cambios realizados a tu página. Para ello enviame un mensaje como \"Ejecutala\" o \"Guarda los cambios\" y se creará una versión optimizada de tu página.")
        dispatcher.utter_message(text="Siempre que quieras podrás volver a modificarla tan solo solicitándolo como te mostré en los pasos anteriores del tutorial.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_8_confirmacion", False), SlotSet("pregunta_8_repetir_confirmacion", False), SlotSet("pregunta_9_confirmacion", True)]

class ActionPregunta9Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_9_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Durante el proceso de creación o modificación de tu página, esta se encuentra en modo edición y no es la versión final de la misma. Para obtener la versión final de tu página debes enviarme un mensaje como \"Ejecutala\" o \"Guarda los cambios\".")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_9_confirmacion", False), SlotSet("pregunta_9_repetir_confirmacion", True)]

class ActionPregunta10(Action):

    def name(self) -> Text:
        return "action_pregunta_10"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Si por algún motivo queres apagar tu página web, solo debes pedirmelo enviando un mensaje como \"Apagala\" o \"Quiero que apagues $$nombre-pagina$$\".")
        dispatcher.utter_message(text="Podrás volver a poner tu página en ejecución si me pides que la ejecute, tal como te expliqué en el paso anterior del tutorial.")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_9_confirmacion", False), SlotSet("pregunta_9_repetir_confirmacion", False), SlotSet("pregunta_10_confirmacion", True)]

class ActionPregunta10Repetir(Action):

    def name(self) -> Text:
        return "action_pregunta_10_repetir"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="Podes apagar tu página para que esta no esté disponible para otros usuarios. Si en otro momento deseas que esta vuelva a estar en línea, podes pedirmelo con un mensaje como \"Ejecutala\".")
        dispatcher.utter_message(text="¿Entendido?")
        return [SlotSet("pregunta_10_confirmacion", False), SlotSet("pregunta_10_repetir_confirmacion", True)]

class ActionTerminarTutorial(Action):

    def name(self) -> Text:
        return "action_terminar_tutorial"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        dispatcher.utter_message(text="¡Felicitaciones " + str(tracker.get_slot("nombre_usuario")) + ", terminaste el tutorial! Ya estas listo para crear tu primera página web")
        dbm.set_user_tutorial(tracker.sender_id)
        return [SlotSet("hizo_tutorial", True), SlotSet("pregunta_4_confirmacion", False), SlotSet("pregunta_4_repetir_confirmacion", False), SlotSet("pregunta_tutorial", False), SlotSet("inicia_tutorial", False)]


class ActionAvisame(Action):

    def name(self) -> Text:
        return "action_avisame"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
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