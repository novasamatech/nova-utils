from __future__ import annotations

from collections import defaultdict
from typing import List, Callable

from scripts.utils.chain_model import Chain
from scripts.xcm_transfers.xcm.registry.parachain import Parachain
from scripts.xcm_transfers.xcm.registry.reserve_location import ReserveLocations
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain


class ConsensusSystem:
    relay: XcmChain
    parachains: List[XcmChain]

    _parachains_by_para_id: dict[int, XcmChain]
    _all_chains: List[XcmChain]

    def __init__(self, relay: XcmChain, parachains: List[XcmChain]):
        self.relay = relay
        self.parachains = parachains

        self._all_chains = [relay] + parachains
        self._parachains_by_para_id = self._associate_parachains_by_id(self.parachains)

    def consensus_chains(self) -> List[XcmChain]:
        return self._all_chains

    def get_parachain(self, parachain_id: int | None) -> XcmChain:
        if parachain_id is None:
            return self.relay

        return self._parachains_by_para_id[parachain_id]

    def get_parachain_or_none(self, parachain_id: int | None) -> XcmChain | None:
        if parachain_id is None:
            return self.relay

        return self._parachains_by_para_id.get(parachain_id, None)

    @staticmethod
    def _associate_parachains_by_id(all_parachains: List[XcmChain]) -> dict[int, XcmChain]:
        return {xcm_chain.parachain_id: xcm_chain for xcm_chain in all_parachains}


class XcmRegistry:
    reserves: ReserveLocations
    consensus_systems: List[ConsensusSystem]

    _consensus_systems_by_relay: dict[str, ConsensusSystem]

    _chains_by_id: dict[str, XcmChain]
    _chains: List[XcmChain]

    def __init__(
            self,
            all_chains: List[XcmChain],
            reserves_constructor: Callable[[XcmRegistry], ReserveLocations],
    ):
        self.reserves = reserves_constructor(self)

        self.consensus_systems = self._detect_consensus_systems(all_chains)
        self._consensus_systems_by_relay = self._associate_consensus_systems_by_relay_id(self.consensus_systems)

        self._chains = self._get_all_chains(self.consensus_systems)
        self._chains_by_id = self._associate_chains_by_id(self._chains)

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
    def _get_all_chains(consensus_systems: List[ConsensusSystem]) -> List[XcmChain]:
        return [chain for consensus_system in consensus_systems for chain in consensus_system.consensus_chains()]

    @staticmethod
    def _associate_consensus_systems_by_relay_id(
            consensus_systems: List[ConsensusSystem]
    ) -> dict[str, ConsensusSystem]:
        return {consensus_system.relay.chain.chainId: consensus_system for consensus_system in consensus_systems}

    @staticmethod
    def _associate_chains_by_id(all_chains: List[XcmChain]) -> dict[str, XcmChain]:
        return {xcm_chain.chain.chainId: xcm_chain for xcm_chain in all_chains}

    @staticmethod
    def _detect_consensus_systems(all_chains: List[XcmChain]) -> List[ConsensusSystem]:
        parachains_by_relay = defaultdict(list)

        for chain in all_chains:
            parent_id = chain.chain.parentId
            if parent_id is None:
                continue

            parachains_by_relay[parent_id].append(chain)

        consensus_systems = []

        for relay_id, parachains in parachains_by_relay.items():
            relay = next((chain for chain in all_chains if chain.chain.chainId == relay_id), None)
            if relay is None:
                continue

            consensus_systems.append(ConsensusSystem(relay, parachains))


        return consensus_systems
