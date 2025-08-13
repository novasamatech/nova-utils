from __future__ import annotations

from dataclasses import dataclass
from typing import List

from scalecodec import GenericCall, GenericEvent

from scripts.xcm_transfers.xcm.dry_run.errors import is_xcm_run_error, handle_xcm_run_error_execution_result, \
    is_call_run_error, handle_call_run_error_execution_result
from scripts.xcm_transfers.xcm.dry_run.events.xcm import find_sent_xcm, check_paid_delivery_fee
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.versioned_xcm import VerionsedXcm
from scripts.xcm_transfers.xcm.versioned_xcm_builder import is_receive_teleported_asset


# Returns dry run effects if successful. Throws otherwise
def dry_run_xcm(chain: XcmChain, xcm: VerionsedXcm, origin: VerionsedXcm) -> dict:
    dry_run_effects = chain.access_substrate(
        lambda substrate: substrate.runtime_call(api="DryRunApi", method="dry_run_xcm",
                                                 params={"origin_location": origin.versioned,
                                                         "xcm": xcm.versioned})).value["Ok"]
    execution_result = dry_run_effects["execution_result"]

    if is_xcm_run_error(execution_result):
        handle_xcm_run_error_execution_result(execution_result)
    else:
        return dry_run_effects

@dataclass
class IntermediateXcmDryRunResult:
    forwarded_xcm: VerionsedXcm
    paid_delivery_fee: bool

# Returns forwarded xcm if successful. Throws otherwise
def dry_run_intermediate_xcm(
        chain: XcmChain,
        xcm: VerionsedXcm,
        origin: VerionsedXcm,
        final_destination_account: str
) -> IntermediateXcmDryRunResult:
    dry_run_effects = dry_run_xcm(chain, xcm, origin)
    forwarded_xcm = find_sent_xcm(chain, dry_run_effects, final_destination_account)
    paid_delivery_fee = check_paid_delivery_fee(chain, dry_run_effects)

    return IntermediateXcmDryRunResult(forwarded_xcm, paid_delivery_fee)

# Returns emitted events if successful. Throws otherwise
def dry_run_final_xcm(chain: XcmChain, xcm: VerionsedXcm, origin: VerionsedXcm) -> List[dict]:
    dry_run_effects = dry_run_xcm(chain, xcm, origin)

    return dry_run_effects["emitted_events"]

@dataclass
class CallDryRunResult:
    forwarded_xcm: VerionsedXcm
    paid_delivery_fee: bool

    def uses_teleport(self) -> bool:
        instructions: List[dict] = self.forwarded_xcm.unversioned

        return any((instruction for instruction in instructions if is_receive_teleported_asset(instruction)))


def dry_run_call(
        chain: XcmChain,
        call: GenericCall,
        result_xcms_version: int,
        origin: dict
) -> dict:
    return chain.access_substrate(
        lambda substrate: substrate.runtime_call(api="DryRunApi", method="dry_run_call",
                                                 params={
                                                     "origin_caller": origin,
                                                     "call": call,
                                                     "result_xcms_version": result_xcms_version
                                                 })).value


def dry_run_xcm_call(
        chain: XcmChain,
        call: GenericCall,
        result_xcms_version: int,
        origin: dict,
        final_destination_account: str
) -> CallDryRunResult:
    dry_run_result = dry_run_call(chain, call, result_xcms_version, origin)

    dry_run_effects = dry_run_result["Ok"]
    execution_result = dry_run_effects["execution_result"]

    if is_call_run_error(execution_result):
        handle_call_run_error_execution_result(chain, execution_result)
    else:
        forwarded_xcm = find_sent_xcm(chain, dry_run_effects, final_destination_account)
        paid_delivery_fee = check_paid_delivery_fee(chain, dry_run_effects)

        return CallDryRunResult(forwarded_xcm, paid_delivery_fee)
