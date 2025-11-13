from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Dict

from scalecodec import GenericCall

CallValue = Dict[str, object]
CallVisitor = Callable[[CallValue], None]

def visit_nested_calls(value, call_visitor: CallVisitor) -> None:
    match value:
        case list():
            _visit_nested_calls_in_list(value, call_visitor)
        case dict():
            _visit_nested_calls_in_dict(value, call_visitor)
        case GenericCall():
            _visit_nested_calls_in_call(value, call_visitor)

def _visit_nested_calls_in_call(value: Dict, call_visitor: CallVisitor) -> None:
    call_visitor(value)

    for arg in value["call_args"]:
        arg_value = arg["value"]
        visit_nested_calls(arg_value, call_visitor)


def _visit_nested_calls_in_list(value: List, call_visitor: CallVisitor) -> None:
    for arg_item in value:
        visit_nested_calls(arg_item, call_visitor)

def _visit_nested_calls_in_dict(value: Dict, call_visitor: CallVisitor) -> None:
    if 'call_args' in value:
        _visit_nested_calls_in_call(value, call_visitor)
        return

    for arg_item in value.values():
        visit_nested_calls(arg_item, call_visitor)


