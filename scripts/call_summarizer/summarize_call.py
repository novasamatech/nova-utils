import json
from typing import Callable, List, Dict

from scalecodec import GenericCall

from scripts.call_summarizer.call_visitor import visit_nested_calls
from scripts.call_summarizer.docs import collect_call_docs
from scripts.utils.chain_registry import ChainRegistry

chain_registry = ChainRegistry.create_latest_prod()

hydration = chain_registry.get_chain("afdc188f45c71dacbaa0b62e16a91f726c7b8699a9748cdf715459de6b7f366d")
hydration.create_connection()
api = hydration.substrate

hex_call = "0x1d005a1daf6281654754e3c1dda5a8e8593882b731757c390229943e754308e29d620043007b0000000000000000e1f5050000000000000000000000006400000000000000000000000000000008037b00000001000000020c0000000100000000000000"

decoded_call: Dict = api.decode_scale("GenericCall", hex_call, return_scale_obj=True)
print(json.dumps(decoded_call, indent=2, default=str))

# def cleanup_call(call: Dict):
#     del call['call_index']
#     del call['call_hash']
#
#     for arg in call['call_args']:
#         del arg['type']
#
#
# call_docs = collect_call_docs(api, decoded_call)
# # visit_nested_calls(decoded_call, cleanup_call)
#
# print("Json representation of the call:")
# print(json.dumps(decoded_call, indent=2, default=vars))
# print("Calls documentation:")
# print(json.dumps(call_docs, indent=2, default=vars))
