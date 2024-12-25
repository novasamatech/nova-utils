from typing import List, Callable


def find_event(events: List, event_module: str, event_name: str) -> dict | None:
    matching_events = find_events(events, event_module, event_name)
    return next(iter(matching_events), None)

def find_events(events: List, event_module: str, event_name: str) -> List[dict]:
    return [event for event in events if event["module_id"] == event_module and event["event_id"] == event_name]

def find_event_with_attributes(events: List, event_module: str, event_name: str, attributes_filter: Callable[[dict], bool]) -> dict | None:
    matching_events = find_events(events, event_module, event_name)
    return next((e for e in matching_events if attributes_filter(e["attributes"])), None)