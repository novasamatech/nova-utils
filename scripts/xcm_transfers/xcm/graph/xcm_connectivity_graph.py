from __future__ import annotations

from typing import List, Dict, Tuple

from scripts.utils.chain_model import ChainAsset
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.registry.xcm_registry import XcmRegistry
from scripts.xcm_transfers.xcm.xcm_transfer_direction import XcmTransferDirection


class XcmChainConnectivityGraph:
    _graph: Dict[str, List[str]]
    _registry: XcmRegistry

    def __init__(self, registry: XcmRegistry, hrmp_channels: List[Tuple[int, int]]) -> None:
        self._graph = _construct_chain_graph(registry, hrmp_channels)
        self._registry = registry

    def has_connection(self, origin_chain_id: str, destination_chain_id: str) -> bool:
        origin_directions = self._graph.get(origin_chain_id, [])
        return destination_chain_id in origin_directions

    def _has_transfer_path(self, potential_destination: XcmTransferDirection) -> bool:
        reserve = self._registry.reserves.get_reserve_or_none(potential_destination.origin_asset)
        if reserve is None:
            return False

        reserve_chain_id = reserve.reserve_chain_id()

        origin_chain_id = potential_destination.origin_chain.chain.chainId
        destination_chain_id = potential_destination.destination_chain.chain.chainId

        if origin_chain_id != reserve_chain_id and destination_chain_id != reserve_chain_id:
            has_path_to_reserve = self.has_connection(origin_chain_id, reserve_chain_id)
            has_path_from_reserve = self.has_connection(reserve_chain_id, destination_chain_id)

            return has_path_to_reserve and has_path_from_reserve
        else:
            return self.has_connection(origin_chain_id, destination_chain_id)

    def _get_matched_origin_and_destination_asset_pairs(
            self,
            origin_chain: XcmChain,
            destination_chain: XcmChain,
    ) -> List[Tuple[ChainAsset, ChainAsset]]:
        unified_destination_ids = {asset.unified_symbol():asset for asset in destination_chain.chain.assets}

        result = []

        for asset in origin_chain.chain.assets:
            unified_symbol = asset.unified_symbol()
            destination_asset = unified_destination_ids.get(unified_symbol, None)

            if destination_asset is not None:
                result.append((asset, destination_asset))

        return result

    def construct_potential_directions(self) -> List[XcmTransferDirection]:
        result = []

        for origin in self._registry.all_chains():
            for destination in self._registry.all_chains():
                if origin.chain.chainId == destination.chain.chainId:
                    continue

                matched_asset_pairs = self._get_matched_origin_and_destination_asset_pairs(origin, destination)

                for (origin_asset, destination_asset) in matched_asset_pairs:
                    potential_destination = XcmTransferDirection(origin, origin_asset, destination, destination_asset)

                    if self._has_transfer_path(potential_destination):
                        result.append(potential_destination)

        return result

    @staticmethod
    def construct_default(xcm_registry: XcmRegistry) -> XcmChainConnectivityGraph:
        hrmp_channels = _fetch_hrmp_channels(xcm_registry.relay)
        return XcmChainConnectivityGraph(xcm_registry, hrmp_channels)


def _fetch_hrmp_channels(relay: XcmChain) -> List[Tuple[int, int]]:
    hrmp_channels_map = relay.access_substrate(lambda s: s.query_map(module="Hrmp", storage_function="HrmpChannels"))
    return [result[0].value for result in hrmp_channels_map]

def _construct_chain_graph(
        registry: XcmRegistry,
        hrmp_channels: List[Tuple[int, int]],
) -> Dict[str, List[str]]:
    relay = registry.relay
    result: Dict[str, List[str]] = {}

    def add_edge_by_id(origin: str, destination: str):
        edges = result.get(origin)
        if edges is None:
            result[origin] = [destination]
        else:
            edges.append(destination)

    def add_edge_by_chain(origin: XcmChain, destination: XcmChain):
        add_edge_by_id(origin.chain.chainId, destination.chain.chainId)

    # relay is accessible from each parachain
    for parachain in registry.parachains:
        add_edge_by_chain(relay, parachain)
        add_edge_by_chain(parachain, relay)

    # add all supported channels
    for channel in hrmp_channels:
        origin = registry.get_parachain_or_none(channel["recipient"])
        destination = registry.get_parachain_or_none(channel["sender"])

        if origin is None or destination is None:
            continue

        add_edge_by_chain(origin, destination)

    return result
