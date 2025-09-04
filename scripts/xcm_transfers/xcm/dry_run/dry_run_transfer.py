from __future__ import annotations

import functools
from dataclasses import dataclass
from time import sleep

from scalecodec import GenericCall
from substrateinterface import SubstrateInterface

from scripts.xcm_transfers.utils.fix_scale_codec import fix_tuple_encoding, fix_substrate_interface
from scripts.xcm_transfers.utils.weight import Weight
from scripts.xcm_transfers.xcm.call_payment.call_payment_api import calculate_call_weight
from scripts.xcm_transfers.xcm.dry_run.dry_run_api import dry_run_xcm_call, dry_run_final_xcm, dry_run_call
from scripts.xcm_transfers.utils.log import debug_log, warn_log
from scripts.xcm_transfers.xcm.dry_run.dry_run_api import dry_run_intermediate_xcm
from scripts.xcm_transfers.xcm.dry_run.errors import extract_dispatch_error_message
from scripts.xcm_transfers.xcm.dry_run.events.deposit import find_deposit_amount
from scripts.xcm_transfers.xcm.dry_run.fund import fund_account_and_then
from scripts.xcm_transfers.xcm.dry_run.origins import root_origin
from scripts.xcm_transfers.xcm.registry.transfer_type import determine_transfer_type
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.registry.xcm_registry import XcmRegistry
from scripts.xcm_transfers.xcm.versioned_xcm import VerionsedXcm
from scripts.xcm_transfers.xcm.versioned_xcm_builder import assets, xcm_program, asset_id, deposit_asset
from scripts.xcm_transfers.xcm.xcm_transfer_direction import XcmTransferDirection


class TransferDryRunner:
    _registry: XcmRegistry

    def __init__(self, registry: XcmRegistry):
        self._registry = registry

        fix_substrate_interface()

    def dry_run_transfer(self, transfer_direction: XcmTransferDirection) -> DryRunTransferResult:
        origin_chain, chain_asset, destination_chain, destination_asset = transfer_direction.origin_chain, transfer_direction.origin_asset, transfer_direction.destination_chain, transfer_direction.destination_asset

        print(
            f"Dry running transfer of {chain_asset.symbol} from {origin_chain.chain.name} to {destination_chain.chain.name}")

        amount = 100
        sender = _dry_run_account_for_chain(origin_chain)
        recipient = _dry_run_account_for_chain(destination_chain)

        transfer_type = determine_transfer_type(self._registry, origin_chain, destination_chain, chain_asset)

        token_location_origin = self._registry.reserves.relative_reserve_location(chain_asset, pov_chain=origin_chain)

        dest = origin_chain.sibling_location_of(destination_chain).versioned
        assets_param = assets(token_location_origin, amount=chain_asset.planks(amount)).versioned
        assets_transfer_type = transfer_type.transfer_type_call_param()
        remote_fees_id_param = asset_id(token_location_origin).versioned

        remote_reserve_chain = transfer_type.check_remote_reserve()

        custom_xcm_on_dest = xcm_program([
            deposit_asset(recipient, evm=destination_chain.chain.has_evm_addresses())
        ]).versioned

        weight_limit = "Unlimited"

        debug_log(f"{dest=}")
        debug_log(f"{assets_param=}")
        debug_log(f"{assets_transfer_type=}")
        debug_log(f"{remote_fees_id_param=}")
        debug_log(f"{weight_limit=}")
        debug_log(f"{custom_xcm_on_dest=}")

        debug_log("\n------------------\n")

        def transfer_assets_call(substrate: SubstrateInterface) -> GenericCall:
            return substrate.compose_call(
                call_module=origin_chain.xcm_pallet_alias(),
                call_function="transfer_assets_using_type_and_then",
                call_params={
                    "dest": dest,
                    "assets": assets_param,
                    "assets_transfer_type": assets_transfer_type,
                    "remote_fees_id": remote_fees_id_param,
                    "fees_transfer_type": assets_transfer_type,
                    "weight_limit": weight_limit,
                    "custom_xcm_on_dest": custom_xcm_on_dest
                }
            )

        call = origin_chain.access_substrate(
            lambda s: fund_account_and_then(s, origin_chain, chain_asset, account=sender, amount=amount * 10,
                                            next_call=transfer_assets_call(s))
        )

        _check_origin_call_weight(call, origin_chain)
        supports_xcm_execute = _detect_supports_xcm_execute(origin_chain)

        origin_dry_run_result = dry_run_xcm_call(
            chain=origin_chain,
            call=call,
            origin=root_origin(),
            result_xcms_version=VerionsedXcm.default_xcm_version(),
            final_destination_account=recipient
        )
        message_to_next_hop = origin_dry_run_result.forwarded_xcm
        paid_delivery_fee = origin_dry_run_result.paid_delivery_fee
        uses_teleport = origin_dry_run_result.uses_teleport()

        debug_log(f"Transfer successfully initiated on {origin_chain.chain.name},"
                  f" paid delivery: {paid_delivery_fee},"
                  f" uses teleport: {uses_teleport},"
                  f" message: {message_to_next_hop}")
        debug_log("\n------------------\n\n")

        message_to_destination: VerionsedXcm
        origin_on_destination: VerionsedXcm

        if remote_reserve_chain is not None:
            message_to_reserve = message_to_next_hop
            origin_on_reserve = remote_reserve_chain.sibling_location_of(origin_chain)

            debug_log(f"{origin_on_reserve.versioned=}")

            reserve_dry_run_result = dry_run_intermediate_xcm(chain=remote_reserve_chain, xcm=message_to_reserve,
                                                              origin=origin_on_reserve,
                                                              final_destination_account=recipient)

            message_to_destination = reserve_dry_run_result.forwarded_xcm
            paid_delivery_fee = paid_delivery_fee or reserve_dry_run_result.paid_delivery_fee

            debug_log(
                f"Transfer successfully handled by reserve chain {remote_reserve_chain.chain.name},"
                f"paid delivery: {reserve_dry_run_result.paid_delivery_fee}"
                f" message: {message_to_reserve.unversioned}\n"
            )

            origin_on_destination = destination_chain.sibling_location_of(remote_reserve_chain)
        else:
            origin_on_destination = destination_chain.sibling_location_of(origin_chain)
            message_to_destination = message_to_next_hop

        debug_log("\n------------------\n")

        destination_events = dry_run_final_xcm(destination_chain, message_to_destination, origin_on_destination)
        deposited_amount = find_deposit_amount(destination_events, destination_asset, recipient)
        if deposited_amount is None:
            raise Exception(f"Deposited amount was not found, final events: {destination_events}")

        result = DryRunTransferResult(
            paid_delivery_fee=paid_delivery_fee,
            supports_xcm_execute=supports_xcm_execute,
            uses_teleport=uses_teleport
        )

        debug_log(
            f"Transfer successfully finished on {destination_chain.chain.name}, result: {result}")

        return result


def _check_origin_call_weight(
        call: GenericCall,
        xcm_chain: XcmChain,
):
    try:
        weight = calculate_call_weight(call, xcm_chain)
    except Exception as e:
        warn_log(f"Could not calculate call weight. Exception message: {e}")
        return

    if weight.is_max_by_any_dimension():
        raise Exception(f"Call weight {weight} exceeds maximum by some dimension")


@functools.cache
def _detect_supports_xcm_execute(xcm_chain: XcmChain) -> bool:
    dry_run_result: dict

    try:
        dry_run_result = xcm_chain.chain.access_substrate(lambda s: _dry_run_empty_xcm_execute(xcm_chain, s))
    except Exception as e:
        warn_log(f"Could not detect support xcm execute status: {e}")
        # Something unexpected happened during our fake dry run
        # Return False here to allow main dry run process to run in any case
        return False

    execution_result = dry_run_result["Ok"]['execution_result']
    error = extract_xcm_execute_error(execution_result, xcm_chain)

    if error is None:
        print(f"Xcm execute status OK")
    else:
        print(f"Xcm execute status error: {error}")

    return error is None


def extract_xcm_execute_error(execution_result: dict, xcm_chain: XcmChain) -> str | None:
    if "Ok" in execution_result:
        return None

    error = execution_result["Error"]["error"]
    error_message = extract_dispatch_error_message(xcm_chain, error)
    # There is some error, but it is not related to xcm execute filter. Probably because we are using empty xcm message
    # dry run from an empty account. Consider such cases as Ok
    if "Filtered" not in error_message:
        return None

    return error_message


def _dry_run_empty_xcm_execute(xcm_chain: XcmChain, substrate: SubstrateInterface) -> dict:
    call = substrate.compose_call(
        call_module=xcm_chain.xcm_pallet_alias(),
        call_function="execute",
        call_params={
            "message": xcm_program([]).versioned,
            "max_weight": Weight.zero().to_sdk_value()
        }
    )

    return dry_run_call(xcm_chain, call, VerionsedXcm.default_xcm_version(), root_origin())


@dataclass
class DryRunTransferResult:
    paid_delivery_fee: bool
    supports_xcm_execute: bool
    uses_teleport: bool


_substrate_account = "13mp1WEs72kbCBF3WKcoK6Hfhu2HHZGpQ4jsKCZbfd6FoRvH"
_evm_account = "0x0c7485f4AA235347BDE0168A59f6c73C7A42ff2C"


def _dry_run_account_for_chain(chain: XcmChain) -> str:
    if chain.chain.has_evm_addresses():
        return _evm_account
    else:
        return _substrate_account
