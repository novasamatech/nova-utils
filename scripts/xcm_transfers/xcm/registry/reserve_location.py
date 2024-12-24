from typing import Tuple, Callable, List

from scripts.utils.chain_model import ChainAsset
from scripts.xcm_transfers.xcm.multi_location import GlobalMultiLocation
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.versioned_xcm import VerionsedXcm
from scripts.xcm_transfers.xcm.versioned_xcm_builder import multi_location_from

from collections import defaultdict


class ReserveLocation:
    _reserve_chain: str
    _asset_location: GlobalMultiLocation

    def __init__(
            self,
            reserve_chain_id: str,
            asset_location: GlobalMultiLocation,
            get_chain: Callable[[str], XcmChain | None],
    ):
        self._reserve_chain_id = reserve_chain_id
        self._asset_location = asset_location
        self.get_chain_or_none = get_chain

    def parachain_id(self) -> int | None:
        return self.reserve_chain().parachain_id

    def reanchor(self, pov_chain: XcmChain) -> VerionsedXcm:
        reanchored_location = self._asset_location.reanchor(pov_chain.global_location())
        return multi_location_from(reanchored_location)

    def reserve_chain(self) -> XcmChain:
        chain = self.get_chain_or_none(self._reserve_chain_id)
        if chain is None:
            raise Exception(f"Reserve chain {self._reserve_chain_id} not found")

        return chain

    def reserve_chain_or_none(self) -> XcmChain:
        return self.get_chain_or_none(self._reserve_chain_id)

    def reserve_chain_id(self) -> str:
        return self._reserve_chain_id


class ReserveLocations:
    _locations_by_reserve_id: dict[str, ReserveLocation]

    # By default, asset reserve id is equal to its symbol
    # This mapping allows to override that for cases like multiple reserves (Statemine & Polkadot for DOT)
    _asset_reserve_override: dict[Tuple[str, int], str]

    def __init__(
            self,
            locations_by_reserve_id: dict[str, ReserveLocation],
            asset_reserve_override: dict[Tuple[str, int], str],
    ):
        self._locations_by_reserve_id = locations_by_reserve_id
        self._asset_reserve_override = asset_reserve_override


    def get_reserve(self, chain_asset: ChainAsset) -> ReserveLocation:
        reserve_id = self._get_reserve_id(chain_asset)
        return self._locations_by_reserve_id[reserve_id]

    def get_reserve_or_none(self, chain_asset: ChainAsset) -> ReserveLocation | None:
        reserve_id = self._get_reserve_id(chain_asset)
        return self._locations_by_reserve_id.get(reserve_id, None)

    def _get_reserve_id(self, chain_asset: ChainAsset) -> str | None:
        symbol = chain_asset.unified_symbol()

        override = self._asset_reserve_override.get(chain_asset.full_chain_asset_id(), None)
        return override if override is not None else symbol

    def relative_reserve_location(self, chain_asset: ChainAsset, pov_chain: XcmChain) -> VerionsedXcm:
        reserve = self.get_reserve(chain_asset)
        return reserve.reanchor(pov_chain)

    def dump_overrides(self) -> dict[str, dict[str]]:
        overrides_as_dict = defaultdict(dict)

        for (chain_id, asset_id), reserve_location in self._asset_reserve_override.items():
            chain_overrides = overrides_as_dict[chain_id]
            chain_overrides[asset_id] = reserve_location
            overrides_as_dict[chain_id] = chain_overrides

        return overrides_as_dict