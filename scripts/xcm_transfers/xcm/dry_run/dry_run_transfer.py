from __future__ import annotations

from dataclasses import dataclass

from scalecodec import GenericCall
from substrateinterface import SubstrateInterface

from scripts.xcm_transfers.utils.fix_scale_codec import fix_scale_codec
from scripts.xcm_transfers.xcm.dry_run.dry_run_api import dry_run_xcm_call, dry_run_final_xcm
from scripts.xcm_transfers.utils.log import debug_log
from scripts.xcm_transfers.xcm.dry_run.dry_run_api import dry_run_intermediate_xcm
from scripts.xcm_transfers.xcm.dry_run.events.deposit import find_deposit_amount
from scripts.xcm_transfers.xcm.dry_run.fund import fund_account_and_then
from scripts.xcm_transfers.xcm.dry_run.origins import root_origin
from scripts.xcm_transfers.xcm.registry.transfer_type import determine_transfer_type
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.registry.xcm_registry import XcmRegistry
from scripts.xcm_transfers.xcm.versioned_xcm import VerionsedXcm
from scripts.xcm_transfers.xcm.versioned_xcm_builder import assets
from scripts.xcm_transfers.xcm.xcm_transfer_direction import XcmTransferDirection

class TransferDryRunner:

    _registry: XcmRegistry

    def __init__(self, registry: XcmRegistry):
        self._registry = registry

        fix_scale_codec()

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

        remote_reserve_chain = transfer_type.check_remote_reserve()

        beneficiary = destination_chain.account_location(recipient).versioned

        fee_asset_item = 0
        weight_limit = "Unlimited"

        debug_log(f"{transfer_type=}")
        debug_log(f"{dest=}")
        debug_log(f"{beneficiary=}")
        debug_log(f"{assets_param=}")
        debug_log(f"{fee_asset_item=}")
        debug_log(f"{weight_limit=}")

        debug_log("\n------------------\n")

        def transfer_assets_call(substrate: SubstrateInterface) -> GenericCall:
            return substrate.compose_call(
                call_module=origin_chain.xcm_pallet_alias(),
                call_function="transfer_assets",
                call_params={
                    "dest": dest,
                    "assets": assets_param,
                    "beneficiary": beneficiary,
                    "fee_asset_item": fee_asset_item,
                    "weight_limit": weight_limit
                }
            )

        call = origin_chain.access_substrate(
            lambda s: fund_account_and_then(s, origin_chain, chain_asset, account=sender, amount=amount * 10,
                                            next_call=transfer_assets_call(s))
        )

        origin_dry_run_result = dry_run_xcm_call(
            chain=origin_chain,
            call=call,
            origin=root_origin(),
            result_xcms_version=VerionsedXcm.default_xcm_version(),
            final_destination_account=recipient
        )
        message_to_next_hop = origin_dry_run_result.forwarded_xcm
        paid_delivery_fee = origin_dry_run_result.paid_delivery_fee

        debug_log(f"Transfer successfully initiated on {origin_chain.chain.name},"
                  f" paid delivery: {paid_delivery_fee},"
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
            execution_fee=amount - deposited_amount,
            paid_delivery_fee=paid_delivery_fee
        )

        debug_log(
            f"Transfer successfully finished on {destination_chain.chain.name}, result: {result}")

        return result

@dataclass
class DryRunTransferResult:
    execution_fee: float
    paid_delivery_fee: bool

_substrate_account = "13mp1WEs72kbCBF3WKcoK6Hfhu2HHZGpQ4jsKCZbfd6FoRvH"
_evm_account = "0x0c7485f4AA235347BDE0168A59f6c73C7A42ff2C"

def _dry_run_account_for_chain(chain: XcmChain) -> str:
    if chain.chain.has_evm_addresses():
        return _evm_account
    else:
        return _substrate_account
