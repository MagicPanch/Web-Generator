from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from generator.Generator import Generator
from generator.PageRunner import PageRunner

running:Dict[Tuple[str, str], PageRunner] = {}

class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        Generator.create_project(user=tracker.sender_id, page_name=tracker.get_slot('page_name'))
        message = "Tu pagina fue creada. Puedes acceder a ella en: "
        dispatcher.utter_message(message)
        self.init_next_app(user=tracker.sender_id, page_name=tracker.get_slot('page_name'))
        return []

    def init_next_app(self, user, page_name):
        running[(user, page_name)] = PageRunner(user, page_name)
        running[(user, page_name)].start()

