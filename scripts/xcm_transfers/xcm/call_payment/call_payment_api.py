from scalecodec import GenericCall

from substrateinterface import SubstrateInterface

from scripts.xcm_transfers.utils.weight import Weight
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain

def calculate_call_weight(call: GenericCall, chain: XcmChain) -> Weight:
    call_info = chain.chain.access_substrate(lambda s: _query_call_info(call, s))
    return Weight.from_sdk_value(call_info["weight"])

def _query_call_info(call: GenericCall, substrate: SubstrateInterface):
    call_length = substrate.encode_scale("GenericCall", call).length

    return substrate.runtime_call(api="TransactionPaymentCallApi", method="query_call_info",
                                                 params={"call": call,
                                                         "len": call_length})
