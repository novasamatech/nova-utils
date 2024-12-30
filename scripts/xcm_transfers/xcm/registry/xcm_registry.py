from __future__ import annotations

from typing import List, Callable

from scripts.utils.chain_model import Chain
from scripts.xcm_transfers.xcm.registry.parachain import Parachain
from scripts.xcm_transfers.xcm.registry.reserve_location import ReserveLocations
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain


class XcmRegistry:
    reserves: ReserveLocations
    relay: XcmChain
    parachains: List[XcmChain]

    _chains_by_id: dict[str, XcmChain]
    _chains: List[XcmChain]
    _parachains_by_para_id: dict[int, XcmChain]

    def __init__(
            self,
            relay: Chain,
            parachains: List[Parachain],
            reserves_constructor: Callable[[XcmRegistry], ReserveLocations],
    ):
        self.reserves = reserves_constructor(self)
        self.relay = XcmChain(relay, parachain_id=None)
        self.parachains = [XcmChain(parachain.chain, parachain_id=parachain.parachain_id) for parachain
                           in parachains]

        self._chains = [self.relay] + self.parachains
        self._chains_by_id = self._associate_chains_by_id(self._chains)
        self._parachains_by_para_id = self._associate_parachains_by_id(self.parachains)

    def get_parachain(self, parachain_id: int | None) -> XcmChain:
        if parachain_id is None:
            return self.relay

        return self._parachains_by_para_id[parachain_id]

    def get_parachain_or_none(self, parachain_id: int | None) -> XcmChain | None:
        if parachain_id is None:
            return self.relay

        return self._parachains_by_para_id.get(parachain_id, None)

    def all_chains(self) -> List[XcmChain]:
        return self._chains

    def get_chain(self, chain_id: str) -> XcmChain:
        return self._chains_by_id[chain_id]

    def get_chain_by_name(self, name: str) -> XcmChain:
        return next((chain for chain in self._chains if chain.chain.name == name))

    def get_chain_or_none(self, chain_id: str) -> XcmChain | None:
        return self._chains_by_id.get(chain_id, None)

    def has_chain(self, chain_id: str) -> bool:
        return chain_id in self._chains_by_id

    @staticmethod
    def _associate_chains_by_id(all_chains: List[XcmChain]) -> dict[str, XcmChain]:
        return {xcm_chain.chain.chainId: xcm_chain for xcm_chain in all_chains}

    @staticmethod
    def _associate_parachains_by_id(all_parachains: List[XcmChain]) -> dict[int, XcmChain]:
        return {xcm_chain.parachain_id: xcm_chain for xcm_chain in all_parachains}
