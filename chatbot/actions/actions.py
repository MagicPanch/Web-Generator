from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests

class ActionCrearPagina(Action):

    def name(self) -> Text:
        return "action_crear_pagina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        url = 'http://127.0.0.1:5000/create-next-app'
        response = requests.get(url, json={'user': tracker.sender_id, 'page_name': tracker.get_slot('page_name')})
        message = "Tu pagina fue creada. Puedes acceder a ella en: " + response.text
        dispatcher.utter_message(message)
        return []
