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
    # Matching the asset id is deliberately skipped: a dry run deposits a single token to the recipient,
    # so the first deposit event for that account is the one we need.
    # pallet-assets emits Issued when tokens are minted (reserve-backed arrival) and Deposited when
    # existing tokens move from a sovereign account (e.g. Snowbridge assets withdrawn back to Asset Hub).
    for event_name, account_attribute in (("Issued", "owner"), ("Deposited", "who")):
        event = find_event_with_attributes(
            events, asset_type.pallet_name(), event_name,
            lambda attrs: decode_account_id(attrs[account_attribute]) == decode_account_id(deposit_account)
        )
        if event is not None:
            return event["attributes"]["amount"]

    return None

def _find_orml_deposit_amount(
        events: List[dict],
        deposit_account: str,
) -> int | None:
    # Matching the asset id is deliberately skipped: a dry run deposits a single token to the recipient,
    # so the first "Deposited" event for that account is the one we need
    event = find_event_with_attributes(events, "Tokens", "Deposited",
                                       lambda attrs: decode_account_id(attrs["who"]) == decode_account_id(deposit_account))
    if event is None:
        return None

    return event["attributes"]["amount"]
