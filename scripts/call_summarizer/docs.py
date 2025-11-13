from dataclasses import dataclass
from typing import Dict, List

from substrateinterface import SubstrateInterface

from scripts.call_summarizer.call_visitor import visit_nested_calls


@dataclass
class CallDocs:
    call_module: str
    call_function: str
    docs: str


def collect_call_docs(api: SubstrateInterface, call: Dict) -> List[CallDocs]:
    calls = set()
    docs = []

    def add_call(call: Dict):
        calls.add((call['call_module'], call['call_function']))

    visit_nested_calls(call, add_call)

    for (method, function) in calls:
        call_metadata = _find_call_metadata(api, method, function)
        docs_item = CallDocs(
            call_module=method,
            call_function=function,
            docs=" ".join(call_metadata['docs'].value)
        )
        docs.append(docs_item)

    return docs


def _find_call_metadata(api: SubstrateInterface, module_name: str, call_function_name: str):
    for pallet in api.metadata.pallets:
        if pallet.name == module_name and pallet.calls:
            for call in pallet.calls:
                if call.name == call_function_name:
                    return call
