from typing import Dict, Text, Any

from rasa_sdk import Tracker
from rasa_sdk.events import SlotSet


def clear_slots(tracker: Tracker, domain: Dict[Text, Any], slots_to_save=[], slots_to_true=[], slots_to_false=[], slots_to_set={}):
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