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

class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        creating_thread = threading.Thread(Generator.create_project(user=tracker.sender_id, page_name=tracker.get_slot('page_name')))
        creating_thread.start()
        message = "Tu pagina fue creada. Puedes acceder a ella en: " + self.init_next_app(user=tracker.sender_id, page_name=tracker.get_slot('page_name'))
        dispatcher.utter_message(message)
        return []

    def init_next_app(self, user, page_name) -> str:
        global current_back_port
        global current_front_port

        # Crear back y front
        running[(user, page_name)] = [None, None]
        running[(user, page_name)][0] = Back(user, page_name, current_back_port)
        running[(user, page_name)][1] = Front(user, page_name, current_front_port, running[(user, page_name)][0].get_app_adress())

        # Incrementar puertos
        #current_back_port = inc_port(current_back_port, CONSTANTS.MAX_BACK_PORT)
        current_front_port = inc_port(current_front_port, CONSTANTS.MAX_FRONT_PORT)

        # Iniciar la ejecucion de los hilos
        #running[(user, page_name)][0].start()
        running[(user, page_name)][1].start()
        # Agregar ruta
        #running[(user, page_name)][0].agregar_ruta('/get-producto', GenericRoutes.get_product, ['GET'])

        return running[(user, page_name)][1].get_page_adress()