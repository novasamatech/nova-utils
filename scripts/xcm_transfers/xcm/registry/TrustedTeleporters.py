from scripts.utils.chain_model import ChainId, FullChainAssetId, ChainAssetId
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain

CustomTeleportsEntry = (ChainId, ChainId, ChainAssetId)  # origin, destination, originAsset


class TrustedTeleporters:
    _custom_teleports: set[CustomTeleportsEntry]

    def __init__(self, custom_teleports: set[CustomTeleportsEntry]):
        self.teleport_overrides = custom_teleports

    def can_teleport(self,
                     origin: XcmChain,
                     destination: XcmChain,
                     origin_asset_id: ChainAssetId
                     ) -> bool:
        if (origin.chain.chainId, destination.chain.chainId, origin_asset_id) in self.teleport_overrides:
            return True

        return self._is_system_teleport(origin, destination)

    @staticmethod
    def _is_system_teleport(origin_chain: XcmChain, destination_chain: XcmChain) -> bool:
        to_relay_teleport = origin_chain.is_system_parachain() and destination_chain.is_relay()
        from_relay_teleport = origin_chain.is_relay() and destination_chain.is_system_parachain()
        system_chains_teleport = origin_chain.is_system_parachain() and destination_chain.is_system_parachain()

        return to_relay_teleport or from_relay_teleport or system_chains_teleport
