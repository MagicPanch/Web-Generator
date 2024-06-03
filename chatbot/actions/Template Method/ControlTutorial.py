import threading
from abc import ABC, abstractmethod
from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from database.DBManager import DBManager
from generator.PageManager import PageManager
from generator.ReactGenerator import ReactGenerator
from generator.TelegramBotManager import TelegramBotManager

dbm = DBManager.get_instance()
pgm = PageManager.get_instance()
rg = ReactGenerator.get_instance()
tbm = TelegramBotManager.get_instance()


class ControlTutorial(Action, ABC):

    @abstractmethod
    def name(self) -> Text:
        pass

    @abstractmethod
    def specific_run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[
        Dict[Text, Any]]:
        pass

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        user_id = tracker.sender_id
        tuto = next(tracker.get_slot("hizo_tutorial"), dbm.get_user_tutorial(user_id))
        if not tuto:
            dispatcher.utter_message(text="Para realizar esta acción primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

        return self.specific_run(dispatcher, tracker, domain)