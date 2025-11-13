from abc import ABC
from typing import TypeVar

T = TypeVar('T')

class TypeValue[T]:
    type_name: str
    value: T

    _

class TypeEnhancer(ABC):

    def enhance_number(self, value):