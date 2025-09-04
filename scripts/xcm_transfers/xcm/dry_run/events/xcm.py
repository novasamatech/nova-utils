from typing import List

from scripts.xcm_transfers.utils.account_id import decode_account_id
from scripts.xcm_transfers.utils.log import debug_log
from scripts.xcm_transfers.xcm.dry_run.errors import extract_dispatch_error_message
from scripts.xcm_transfers.xcm.dry_run.events.base import find_event, find_events
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.versioned_xcm import VerionsedXcm
from scripts.xcm_transfers.xcm.versioned_xcm_builder import xcm_program

class XcmSentEvent:
    _attributes: dict
    sent_message: VerionsedXcm

    def __init__(self, event_data: dict):
        self._attributes = event_data["attributes"]
        self.sent_message = xcm_program(self._attributes["message"])


def find_sent_xcm(
        origin: XcmChain,
        success_dry_run_effects: dict,
        final_destination_account: str
) -> VerionsedXcm:
    emitted_events = success_dry_run_effects["emitted_events"]

    # xcm_sent_event = _find_xcm_sent_event(origin, emitted_events)
    # if xcm_sent_event is not None:
    #     debug_log(f"Found sent xcm in XcmSent event")
    #     return xcm_sent_event.sent_message

    forwarded_xcm = _find_forwarded_xcm(success_dry_run_effects, final_destination_account)
    if forwarded_xcm is not None:
        debug_log(f"Found sent xcm in forwarded xcms")
        return forwarded_xcm


    error = _search_for_error_in_events(origin, emitted_events)
    if error is not None:
        raise Exception(f"Execution failed with {error}")

    raise Exception(f"Sent xcm was not found, got: {success_dry_run_effects}")

def check_paid_delivery_fee(
    origin: XcmChain,
    success_dry_run_effects: dict,
) -> bool:
    emitted_events = success_dry_run_effects["emitted_events"]
    event_data = find_event(emitted_events, event_module=origin.xcm_pallet_alias(), event_name="FeesPaid")

    if event_data is None:
        return False

    fees_multi_assets = event_data['attributes']['fees']
    return len(fees_multi_assets) > 0


def _find_xcm_sent_event(chain: XcmChain, events: List) -> XcmSentEvent | None:
    event_data = find_event(events, event_module=chain.xcm_pallet_alias(), event_name="Sent")
    if event_data is not None:
        return XcmSentEvent(event_data)
    else:
        return None

def _find_forwarded_xcm(
        success_dry_run_effects: dict,
        final_destination_account: str,
) -> VerionsedXcm | None:
    forwarded_xcms = success_dry_run_effects["forwarded_xcms"]

    final_destination_account_id = decode_account_id(final_destination_account)

    for (destination, messages) in forwarded_xcms:
        for message in messages:
            message_program = xcm_program(message)
            extracted_account = _extract_final_beneficiary_from_program(message_program)

            if extracted_account == final_destination_account_id:
                return message_program

    return None


def _search_for_error_in_events(chain: XcmChain, events: List) -> str | None:
    dispatched_as_events = find_events(events, "Utility", "DispatchedAs")

    for dispatched_as_event in dispatched_as_events:
        dispatch_result = dispatched_as_event["attributes"]["result"]

        if "Err" not in dispatch_result:
            continue

        error_description = extract_dispatch_error_message(chain, dispatch_result["Err"])
        return error_description

    return None


def _extract_final_beneficiary_from_program(program: VerionsedXcm) -> str | None:
    for instruction in program.unversioned:
        from_instruction = _extract_final_beneficiary_from_instruction(instruction)
        if from_instruction is not None:
            return from_instruction

    return None


def _get_single_key(instruction: dict | str) -> str | None:
    if type(instruction) is str:
        return None

    if len(instruction) != 1:
        raise Exception(f"Expected a single key dict, got: {instruction}")

    return next(iter(instruction))


def _extract_final_beneficiary_from_instruction(instruction: dict) -> str | None:
    match _get_single_key(instruction):
        case "DepositAsset":
            return _extract_beneficiary_from_location(instruction["DepositAsset"]["beneficiary"])
        case "DepositReserveAsset" | "InitiateReserveWithdraw" | "InitiateTeleport" | "TransferReserveAsset" as key:
            nested_message = instruction[key]["xcm"]
            return _extract_final_beneficiary_from_program(xcm_program(nested_message))
        case _:
            return None


def _extract_beneficiary_from_location(location: dict) -> str | None:
    interior = location["interior"]
    x1_junction: dict

    match _get_single_key(interior):
        # Accounts are always X1
        case "X1":
            x1_junction = interior["X1"]
            # pre-v3 x1 interior is just junction itself, otherwise it is a list of single element
            if type(x1_junction) is list:
                x1_junction = x1_junction[0]
        case _:
            return None

    match _get_single_key(x1_junction):
        case "AccountKey20":
            return x1_junction["AccountKey20"]["key"]
        case "AccountId32":
            return x1_junction["AccountId32"]["id"]
        case _:
            return None
