from abc import ABC, abstractmethod

from scripts.call_summarizer.call_visitor import CallValue


class CallEnhancer(ABC):

    @abstractmethod
    def enhance_call(self, call_value: CallValue):
        pass