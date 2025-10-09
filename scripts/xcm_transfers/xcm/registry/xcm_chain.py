from __future__ import annotations

from typing import Callable, TypeVar, Optional

from substrateinterface import SubstrateInterface

from scripts.utils.chain_model import Chain
from scripts.xcm_transfers.xcm.multi_location import GlobalMultiLocation
from scripts.xcm_transfers.xcm.versioned_xcm import VerionsedXcm
from scripts.xcm_transfers.xcm.versioned_xcm_builder import parachain_junction, multi_location, account_junction, \
    multi_location_from

T = TypeVar('T')
ParachainId = int

xcm_pallet_aliases = ["PolkadotXcm", "XcmPallet"]

class XcmChain:
    chain: Chain
    parachain_id: Optional[ParachainId]

    supports_xcm_payment_api: bool

    def __init__(
            self,
            chain: Chain,
            parachain_id: Optional[ParachainId],
            supports_xcm_payment_api: bool
    ):
        self.chain = chain
        self.parachain_id = parachain_id
        self.supports_xcm_payment_api = supports_xcm_payment_api

    def access_substrate(self, action: Callable[[SubstrateInterface], T]) -> T:
        return self.chain.access_substrate(action)

    def sibling_location_of(self, destination_chain: XcmChain) -> VerionsedXcm:
        relative_location = destination_chain.global_location().reanchor(self.global_location())

        return multi_location_from(relative_location)

    def global_location(self) -> GlobalMultiLocation:
        if self.parachain_id is not None:
            return GlobalMultiLocation([parachain_junction(self.parachain_id)])
        else:
            return GlobalMultiLocation([])

    def account_location(self, account: str):
        return multi_location(parents=0, junctions=[account_junction(account, evm=self.chain.has_evm_addresses())])

    def xcm_pallet_alias(self) -> str:
        result = next((candidate for candidate in xcm_pallet_aliases if
                       self.access_substrate(lambda s: s.get_metadata_module(candidate)) is not None), None)

        if result is None:
            raise Exception(f"No XcmPallet or its aliases has been found. Searched aliases: {xcm_pallet_aliases}")

        return result

    def is_system_parachain(self) -> bool:
        return self.parachain_id is not None and 1000 <= self.parachain_id < 2000

    def is_regular_parachain(self) -> bool:
        return self.parachain_id is not None and self.parachain_id >= 2000

    def is_relay(self) -> bool:
        return self.parachain_id is None
