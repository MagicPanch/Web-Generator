from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
class ActionPrueba(Action):

    def name(self) -> Text:
        return "action_prueba"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        print("sender id: ", tracker.sender_id)

        dispatcher.utter_message(text=("Tu ID es " + str(tracker.sender_id)))
        return []
