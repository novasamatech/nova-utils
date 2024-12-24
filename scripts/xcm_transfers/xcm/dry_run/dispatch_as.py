from scalecodec import GenericCall
from substrateinterface import SubstrateInterface


def compose_dispatch_as(
        substrate: SubstrateInterface,
        origin: dict,
        call: GenericCall
):
    return substrate.compose_call(
        call_module="Utility",
        call_function="dispatch_as",
        call_params={
            "as_origin": origin,
            "call": call
        }
    )