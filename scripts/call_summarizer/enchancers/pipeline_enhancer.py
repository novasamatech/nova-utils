from typing import List

from scripts.call_summarizer.enchancers.call_enhancer import CallEnhancer
from scripts.call_summarizer.call_visitor import CallValue


class PipelineEnhancer(CallEnhancer):

    _delegates: List[CallEnhancer]

    def __init__(self, delegates: List[CallEnhancer]):
        self._delegates = delegates

    def enhance_call(self, call_value: CallValue):
        for delegate in self._delegates:
            delegate.enhance_call(call_value)