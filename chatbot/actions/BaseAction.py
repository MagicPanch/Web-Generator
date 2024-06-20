import threading
import re
from abc import ABC, abstractmethod
from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.executor import CollectingDispatcher

from database.DBManager import DBManager
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
        events = []

        # Verificación del nombre de la página
        page_name = tracker.get_slot("page_name")
        if page_name is None or "&&" not in page_name:
        # No hay nombre de página
            page_name = self.capture_page_name(tracker)
            events.append(SlotSet("page_name", page_name))
        else:
            page_name = page_name[2:len(page_name) - 2].strip()
        print(f"({threading.current_thread().getName()}) --------page_name: {page_name}----")

        # Lógica específica para acciones que no requieren verificación de tutorial
        if self.skip_tuto_verification():
            events += self.handle_action(dispatcher, tracker, domain, user_id, page_name)
            return events

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
            events += self.handle_action(dispatcher, tracker, domain, user_id)
            return events

        # Verificación de la página
        pages = dbm.get_user_pages(user_id)
        print(f"({threading.current_thread().getName()}) --------page_name: {page_name}----")
        if page_name is None:
            events += self.handle_page_error(dispatcher, tracker, domain, pages)
            return events
        else:
            # Hay pagina
            page_doc = dbm.get_page(user_id, page_name)
            print(f"({threading.current_thread().getName()}) --------page_doc.name: {page_doc.name}----")
            if page_doc is None:
                # Esa pagina no pertenece al usuario
                events += self.handle_page_error(dispatcher, tracker, domain, pages)
                return events
        events += self.handle_action(dispatcher, tracker, domain, user_id, page_name, page_doc)
        return events

    @abstractmethod
    def handle_action(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], user_id: Text,
                      page_name: Text = None, page_doc: Any = None, pages: Any = None) -> List[Dict[Text, Any]]:
        pass

    def capture_page_name(self, tracker: Tracker):
        user_input = tracker.latest_message.get("text")
        if "&&" in user_input:
            regex = r"&&([a-zA-Z0-9\-_]+)&&"
            match = re.search(regex, user_input)
            if match:
                return match.group(1)
        return None

    def handle_page_error(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any], pages) -> List[Dict[Text, Any]]:
        if len(pages) > 0:
            buttons = []
            for page in pages:
                buttons.append({"payload": "&&" + str(page.name) + "&&", "title": page.name})
            dispatcher.utter_message(text="¿Sobre qué página te gustaría operar? Te recuerdo que tus páginas son:", buttons=buttons, button_type="vertical")
        else:
            dispatcher.utter_message(text="Antes de realizar operaciones sobre una página, debes crear una.")
            return self.clear_slots(tracker, domain)
        if self.name() == "action_preguntar_nombre_pagina":
            events = self.clear_slots(tracker, domain, slots_to_true=["creando_pagina", "pregunta_nombre"])
        elif self.name() == "action_detener_pagina":
            events = self.clear_slots(tracker, domain, slots_to_true=["pregunta_detencion"])
        elif self.name() == "action_ejecutar_pagina":
            events = self.clear_slots(tracker, domain, slots_to_true=["pregunta_ejecucion"])
        elif self.name() == "action_pedir_productos":
            events = self.clear_slots(tracker, domain, slots_to_true=["agregando_productos", "pregunta_nombre"])
        elif self.name() == "action_crear_pagina":
            events = self.clear_slots(tracker, domain, slots_to_true=["creando_pagina", "pregunta_nombre"])
        elif self.name() == "action_capturar_edicion":
            events = self.clear_slots(tracker, domain, slots_to_true=["pregunta_nombre"], slots_to_save=["componente", "tipo_seccion", "nombre_informativa"])
        elif self.name() == "action_capturar_tipo_seccion":
            events = self.clear_slots(tracker, domain, slots_to_true=["creando_seccion", "pregunta_nombre"], slots_to_save=["tipo_seccion"], slots_to_set=dict({"componente": "seccion"}))
        else:
            events = self.clear_slots(tracker, domain)
        for slot in tracker.slots.keys():
            print(slot + " : " + str(tracker.slots[slot]))
        return events

    def clear_slots(self, tracker: Tracker, domain: Dict[Text, Any], slots_to_save=[], slots_to_true=[], slots_to_false=[], slots_to_set={}):
        events = []
        for slot in domain.get("slots"):
            if slot in slots_to_true:
                events.append(SlotSet(slot, True))
            elif slot in slots_to_false:
                events.append(SlotSet(slot, False))
            elif slot in slots_to_set.keys():
                events.append(SlotSet(slot, slots_to_set.get(slot)))
            elif slot not in slots_to_save:
                if type(tracker.get_slot(slot)) is bool:
                    events.append(SlotSet(slot, False))
                else:
                    events.append(SlotSet(slot, None))
        return events

    def skip_tuto_verification(self) -> bool:
        return True

    def skip_page_verification(self) -> bool:
        return True