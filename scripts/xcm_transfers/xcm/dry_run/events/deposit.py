from typing import List

from scripts.utils.chain_model import ChainAsset, NativeAssetType, StatemineAssetType, OrmlAssetType, \
    UnsupportedAssetType
from scripts.xcm_transfers.utils.account_id import decode_account_id
from scripts.xcm_transfers.xcm.dry_run.events.base import find_event_with_attributes


def find_deposit_amount(
        events: List[dict],
        deposited_asset: ChainAsset,
        deposit_account: str
) -> float | None:
    planks: int | None = None

    match deposited_asset.type:
        case NativeAssetType():
            planks = _find_native_deposit_amount(events, deposit_account)
        case StatemineAssetType() as asset_type:
            planks = _find_statemine_deposit_amount(asset_type, events, deposit_account)
        case OrmlAssetType():
            planks = _find_orml_deposit_amount(events, deposit_account)
        case UnsupportedAssetType():
            raise Exception("Unsupported asset type")

    if planks is None:
        return None

    return deposited_asset.amount(planks)

def _find_native_deposit_amount(
        events: List[dict],
        deposit_account: str,
) -> int | None:
    event = find_event_with_attributes(events, "Balances", "Minted",
                                       lambda attrs: decode_account_id(attrs["who"]) == decode_account_id(deposit_account))
    if event is None:
        return None

    return event["attributes"]["amount"]

def _find_statemine_deposit_amount(
        asset_type: StatemineAssetType,
        events: List[dict],
        deposit_account: str,
) -> int | None:
    # READ_WHEN_CREATING_V8 matching asset id is quite cumbersome here so we dont do it since
    # there should only be one "Issued" event to a recipient account, in the receiving token
    event = find_event_with_attributes(events, asset_type.pallet_name(), "Issued",
                                       lambda attrs: decode_account_id(attrs["owner"]) == decode_account_id(deposit_account))
    if event is None:
        return None

    return event["attributes"]["amount"]

def _find_orml_deposit_amount(
        events: List[dict],
        deposit_account: str,
) -> int | None:
    # READ_WHEN_CREATING_V8 matching asset id is quite cumbersome here so we dont do it since
    # there should only be one "Issued" event to a recipient account, in the receiving token
    event = find_event_with_attributes(events, "Tokens", "Deposited",
                                       lambda attrs: decode_account_id(attrs["who"]) == decode_account_id(deposit_account))
    if event is None:
        return None

    return event["attributes"]["amount"]
