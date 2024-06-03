import threading
from abc import ABC, abstractmethod
from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from database.DBManager import DBManager
from database.collections.general import Page
from generator.PageManager import PageManager
from generator.ReactGenerator import ReactGenerator
from generator.TelegramBotManager import TelegramBotManager

dbm = DBManager.get_instance()
pgm = PageManager.get_instance()
rg = ReactGenerator.get_instance()
tbm = TelegramBotManager.get_instance()


class BaseAction(Action, ABC):

    @abstractmethod
    def name(self) -> Text:
        pass

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global dbm
        print(f"({threading.current_thread().getName()}) ----{self.name().upper()}----")
        user_id = tracker.sender_id

        # Lógica específica para acciones que no requieren verificación de tutorial
        if self.skip_tuto_verification():
            return self.handle_action(dispatcher, tracker, domain, user_id)

        # Verificación del tutorial
        if tracker.get_slot("hizo_tutorial") is not None:
            tuto = tracker.get_slot("hizo_tutorial")
        else:
            tuto = dbm.get_user_tutorial(user_id)
        if not tuto:
            dispatcher.utter_message(text="Para continuar primero debes completar el tutorial. ¿Deseas hacerlo ahora?")
            return [SlotSet("pregunta_tutorial", True)]

        # Lógica específica para acciones que no requieren verificación de página
        if self.skip_page_verification():
            return self.handle_action(dispatcher, tracker, domain, user_id)

        # Verificación de la página
        pages = dbm.get_user_pages(user_id)
        page_name = tracker.get_slot('page_name')
        if not page_name:
            # No hay página
            return self.capture_page_error(dispatcher, pages)
        else:
            # Hay pagina
            page_doc = dbm.get_page(user_id, page_name)
            if not page_doc:
                # Esa pagina no pertenece al usuario
                return self.capture_page_error(dispatcher, pages)

        return self.handle_action(dispatcher, tracker, domain, user_id, page_name, page_doc)

    @abstractmethod
    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        pass

    def capture_page_error(self, dispatcher: CollectingDispatcher, pages) -> List[Dict[Text, Any]]:
        if len(pages) > 0:
            message = "¿Sobre qué página te gustaría operar? Te recuerdo que tus páginas son:\n"
            for page in pages:
                message += str(page.name) + "\n"
        else:
            message = "Antes de realizar operaciones sobre una página, debes crear una."
            dispatcher.utter_message(text=message)
        return [SlotSet("pregunta_nombre", True)]

    def skip_tuto_verification(self) -> bool:
        return True

    def skip_page_verification(self) -> bool:
        return True
