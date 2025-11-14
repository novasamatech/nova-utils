from typing import List, Iterator

from scripts.xcm_transfers.xcm.registry.xcm_registry import XcmRegistry
from scripts.xcm_transfers.xcm.xcm_transfer_direction import XcmTransferDirection


class XcmConfigTraversal:
    xcm_config: dict
    registry: XcmRegistry

    def __init__(self, xcm_config: dict, xcm_registry: XcmRegistry):
        self.xcm_config = xcm_config
        self.registry = xcm_registry

    def collect_config_directions(self) -> List[XcmTransferDirection]:
        return [it for it in self.traverse_known_directions()]

    def traverse_known_directions(self) -> Iterator[XcmTransferDirection]:
        for xcm_chain_config in self.xcm_config["chains"]:
            origin_chain_id = xcm_chain_config["chainId"]
            origin_chain = self.registry.get_chain_or_none(origin_chain_id)
            if origin_chain is None:
                continue

            for origin_asset_config in xcm_chain_config["assets"]:
                origin_asset_id = origin_asset_config["assetId"]
                origin_chain_asset = origin_chain.chain.get_asset_by_id(origin_asset_id)

                reserves = self.registry.reserves.get_reserve_or_none(origin_chain_asset)
                if reserves is None:
                    continue
                reserve_chain = reserves.reserve_chain_or_none()
                if reserve_chain is None:
                    continue

                for transfer_config in origin_asset_config["xcmTransfers"]:
                    destination_chain_id = transfer_config["chainId"]
                    destination_asset_id = transfer_config["assetId"]

                    destination_chain = self.registry.get_chain_or_none(destination_chain_id)
                    if destination_chain is None:
                        continue

                    destination_asset = destination_chain.chain.get_asset_by_id(destination_asset_id)

                    direction = XcmTransferDirection(origin_chain, origin_chain_asset, destination_chain, destination_asset)

                    yield direction
