from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import threading

from generator.Generator import Generator
from generator.PageRunner import PageRunner
from generator.Front import Front
from generator.Back import Back
import generator.GenericRoutes
import CONSTANTS

running:Dict[Tuple[str, str], List[PageRunner]] = {}
current_back_port = CONSTANTS.MIN_BACK_PORT
current_front_port = CONSTANTS.MIN_FRONT_PORT

def inc_port(current, max):
    current = current + 1
    if current > max:
        raise Exception("Se ha alcanzado el máximo número de páginas en ejecución")
    return current

def dec_port(current, min):
    current = current - 1
    if current < min:
        current = min
    return current

class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        creating_thread = threading.Thread(Generator.create_project(user=tracker.sender_id, page_name=tracker.get_slot('page_name')))
        creating_thread.start()
        creating_thread.join()
        print("------------PAGINA CREADA---------")
        message = "Tu pagina fue creada con exito."
        dispatcher.utter_message(message)
        return []

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
        global current_back_port
        global current_front_port
        global running

        # Crear back y front
        running[(user, page_name)] = [None, None]
        #running[(user, page_name)][0] = Back(user, page_name, current_back_port)
        running[(user, page_name)][1] = Front(user, page_name, current_front_port, "") #running[(user, page_name)][0].get_app_adress())

        # Incrementar puertos
        #current_back_port = inc_port(current_back_port, CONSTANTS.MAX_BACK_PORT)
        current_front_port = inc_port(current_front_port, CONSTANTS.MAX_FRONT_PORT)

        # Compilar
        running[(user, page_name)][1].build_page()
        print("------------PAGINA COMPILADA---------")

        # Iniciar la ejecucion de los hilos
        #running[(user, page_name)][0].start()
        running[(user, page_name)][1].start()
        # Agregar ruta
        #running[(user, page_name)][0].agregar_ruta('/get-producto', GenericRoutes.get_product, ['GET'])

        return running[(user, page_name)][1].get_page_adress()

    class ActionDetenerPagina(Action):

        def name(self) -> Text:
            return "action_detener_pagina"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            if (tracker.get_slot('page_name') is None):
                message = "Indicame el nombre de la pagina que deseas detener. Te recuerdo que tus paginas son: "
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
            running[(user, page_name)][1].stop()
            running.pop((user, page_name))

            # Decrementar puertos
            current_front_port = dec_port(current_front_port, CONSTANTS.MIN_FRONT_PORT)
