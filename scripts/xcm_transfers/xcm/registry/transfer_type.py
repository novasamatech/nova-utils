from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union

from scripts.utils.chain_model import ChainAsset
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain

class TransferType(ABC):

    @abstractmethod
    def check_remote_reserve(self) -> Union[XcmChain, None]:
        pass

    @abstractmethod
    def transfer_type_call_param(self) -> dict | str:
        pass

    def __str__(self):
        return self.transfer_type_call_param()


class Teleport(TransferType):

    def check_remote_reserve(self) -> Union[XcmChain, None]:
        return None

    def transfer_type_call_param(self) -> dict | str:
        return "Teleport"


class LocalReserve(TransferType):

    def check_remote_reserve(self) -> Union[XcmChain, None]:
        return None

    def transfer_type_call_param(self) -> dict | str:
        return "LocalReserve"


class DestinationReserve(TransferType):

    def check_remote_reserve(self) -> Union[XcmChain, None]:
        return None

    def transfer_type_call_param(self) -> dict | str:
        return "DestinationReserve"


class RemoteReserve(TransferType):
    _origin_chain: XcmChain
    _reserve_chain: XcmChain

    def __init__(self, origin_chain: XcmChain, reserve_chain: XcmChain):
        self._reserve_chain = reserve_chain
        self._origin_chain = origin_chain

    def check_remote_reserve(self) -> Union[XcmChain, None]:
        return self._reserve_chain

    def transfer_type_call_param(self) -> dict | str:
        return {"RemoteReserve": self._origin_chain.sibling_location_of(self._reserve_chain).versioned}
