from scripts.call_summarizer.enchancers.call_enhancer import CallEnhancer
from scripts.call_summarizer.call_visitor import CallValue


class NativePlanksConverter(CallEnhancer):

    _decimals: int

    def __init__(self, decimals: int):
        self._decimals = decimals

    def enhance_call(self, call_value: CallValue):
        call_value