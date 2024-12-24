from dataclasses import dataclass

from scripts.utils.chain_model import ChainAsset
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain


@dataclass
class XcmTransferDirection:
    origin_chain: XcmChain
    origin_asset: ChainAsset

    destination_chain: XcmChain
    destination_asset: ChainAsset

    def __repr__(self):
        return f"{self.origin_asset.symbol} {self.origin_chain.chain.name} -> {self.destination_chain.chain.name}"
