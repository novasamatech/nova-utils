from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union

from scripts.utils.chain_model import ChainAsset
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.registry.xcm_registry import XcmRegistry


def determine_transfer_type(
        registry: XcmRegistry,
        origin_chain: XcmChain,
        destination_chain: XcmChain,
        chain_asset: ChainAsset
) -> TransferType:
    reserve = registry.reserves.get_reserve(chain_asset)
    reserve_parachain_id = reserve.parachain_id()
    origin_parachain_id = origin_chain.parachain_id

    if _should_use_teleport(origin_chain, destination_chain):
        return Teleport()
    elif origin_parachain_id == reserve_parachain_id:
        return LocalReserve()
    elif destination_chain.parachain_id == reserve_parachain_id:
        return DestinationReserve()
    else:
        reserve_chain = reserve.reserve_chain()
        return RemoteReserve(origin_chain=origin_chain, reserve_chain=reserve_chain, registry=registry)

def _should_use_teleport(origin_chain: XcmChain, destination_chain: XcmChain) -> bool:
        to_relay_teleport = origin_chain.is_system_parachain() and destination_chain.is_relay()
        from_relay_teleport = origin_chain.is_relay() and destination_chain.is_system_parachain()
        system_chains_teleport = origin_chain.is_system_parachain() and destination_chain.is_system_parachain()

        return to_relay_teleport or from_relay_teleport or system_chains_teleport

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
    _registry: XcmRegistry

    def __init__(self, origin_chain: XcmChain, reserve_chain: XcmChain, registry: XcmRegistry):
        self._reserve_chain = reserve_chain
        self._registry = registry
        self._origin_chain = origin_chain

    def check_remote_reserve(self) -> Union[XcmChain, None]:
        return self._reserve_chain

    def transfer_type_call_param(self) -> dict | str:
        return {"RemoteReserve": self._origin_chain.sibling_location_of(self._reserve_chain).versioned}
