from typing import List

from scalecodec import GenericCall, GenericEvent

from scripts.xcm_transfers.xcm.dry_run.errors import is_xcm_run_error, handle_xcm_run_error_execution_result, \
    is_call_run_error, handle_call_run_error_execution_result
from scripts.xcm_transfers.xcm.dry_run.events import find_sent_xcm
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.versioned_xcm import VerionsedXcm

# Returns dry run effects if successful. Throws otherwise
def dry_run_xcm(chain: XcmChain, xcm: VerionsedXcm, origin: VerionsedXcm) -> dict:
    dry_run_effects = chain.access_substrate(
        lambda substrate: substrate.runtime_call(api="DryRunApi", method="dry_run_xcm",
                                                 params={"origin_location": origin.versioned,
                                                         "xcm_transfers": xcm.versioned})).value["Ok"]
    execution_result = dry_run_effects["execution_result"]

    if is_xcm_run_error(execution_result):
        handle_xcm_run_error_execution_result(execution_result)
    else:
        return dry_run_effects

# Returns forwarded xcm if successful. Throws otherwise
def dry_run_intermediate_xcm(
        chain: XcmChain,
        xcm: VerionsedXcm,
        origin: VerionsedXcm,
        final_destination_account: str
) -> VerionsedXcm:
    dry_run_effects = dry_run_xcm(chain, xcm, origin)

    return find_sent_xcm(chain, dry_run_effects, final_destination_account)

# Returns emitted events if successful. Throws otherwise
def dry_run_final_xcm(chain: XcmChain, xcm: VerionsedXcm, origin: VerionsedXcm) -> List[GenericEvent]:
    dry_run_effects = dry_run_xcm(chain, xcm, origin)

    return dry_run_effects["emitted_events"]

def dry_run_xcm_call(
        chain: XcmChain,
        call: GenericCall,
        origin: dict,
        final_destination_account: str
) -> VerionsedXcm:
    dry_run_result = chain.access_substrate(
        lambda substrate: substrate.runtime_call(api="DryRunApi", method="dry_run_call",
                                                 params={"origin_caller": origin, "call": call})).value

    dry_run_effects = dry_run_result["Ok"]
    execution_result = dry_run_effects["execution_result"]

    if is_call_run_error(execution_result):
        handle_call_run_error_execution_result(chain, execution_result)
    else:
        return find_sent_xcm(chain, dry_run_effects, final_destination_account)