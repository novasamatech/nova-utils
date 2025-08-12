from typing import List

from scripts.xcm_transfers.utils.account_id import decode_account_id
from scripts.xcm_transfers.xcm.multi_location import RelativeMultiLocation
from scripts.xcm_transfers.xcm.versioned_xcm import VerionsedXcm, xcm_version_mode_consts


def multi_location(parents: int, junctions: List[dict]) -> VerionsedXcm:
    interior = "Here"

    if len(junctions) > 0:
        interior_variant = f"X{len(junctions)}"

        if VerionsedXcm.default_xcm_version() <= 3 and len(junctions) == 1:
            interior = {interior_variant: junctions[0]}
        else:
            interior = {interior_variant: junctions}

    return VerionsedXcm({"parents": parents, "interior": interior})

def multi_location_from(relative_location: RelativeMultiLocation) -> VerionsedXcm:
    return multi_location(relative_location.parents, relative_location.junctions)

def asset_id(location: VerionsedXcm) -> VerionsedXcm:
    if location.is_v4():
        return location
    else:
        return VerionsedXcm({"Concrete": location.unversioned})


def asset(location: VerionsedXcm, amount: int) -> VerionsedXcm:
    return VerionsedXcm({"id": asset_id(location).unversioned, "fun": {"Fungible": amount}})


def assets(location: VerionsedXcm, amount: int) -> VerionsedXcm:
    return VerionsedXcm([asset(location, amount).unversioned])


def absolute_location(junctions: List[dict]) -> VerionsedXcm:
    return multi_location(parents=0, junctions=junctions)


def xcm_program(message: List[dict] | dict[str, List]) -> VerionsedXcm:
    # List of instructions
    if type(message) is list:
        return VerionsedXcm(message)
    # Versioned program
    else:
        return VerionsedXcm(message, message_version=xcm_version_mode_consts.AlreadyVersioned)


def buy_execution(fees_asset: VerionsedXcm, weight_limit: str | dict = "Unlimited"):
    return {'BuyExecution': {'fees': fees_asset.unversioned, 'weight_limit': weight_limit}}


def deposit_asset(
        beneficiary: str,
        evm: bool
):
    return {"DepositAsset": {"assets": {'Wild': {'AllCounted': 1}},
                             "beneficiary": absolute_location(
                                 junctions=[account_junction(beneficiary, evm)]).unversioned}}


def account_junction(
        account: str,
        evm: bool,
) -> dict:
    account_id = decode_account_id(account)

    if evm:
        return {"AccountKey20": {"network": None, "key": account_id}}
    else:
        return {"AccountId32": {"network": None, "id": account_id}}

def parachain_junction(parachain_id: int) -> dict:
    return {"Parachain": parachain_id}


def is_receive_teleported_asset(instruction: dict) ->bool:
    return "ReceiveTeleportedAsset" in instruction
