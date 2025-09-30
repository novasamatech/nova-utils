import json

from eth_typing import ChainId

from scripts.utils.chain_model import Chain
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.config_setup import get_xcm_config_files

config_files = get_xcm_config_files()
general_config = get_data_from_file(config_files.general_config)

chains_file = get_data_from_file(config_files.chains)
chains = [Chain(it) for it in chains_file]

def find_chain(chainId: ChainId) -> Chain:
    return next((chain for chain in chains if chain.chainId == chainId))

def get_consensus_root(chainId: ChainId) -> Chain:
    chain = find_chain(chainId)
    if chain.parentId is None:
        return chain

    parent = find_chain(chain.parentId)
    return parent

def construct_global_consensus_arg(consensus_root: Chain):
    match consensus_root.chainId:
        case "91b171bb158e2d3848fa23a9f1c25182fb8e20313b2c1eb49219da7a70ce90c3":
            return "Polkadot"
        case "b0a8d493285c2df73290dfb7e61f870f17b41801197a149ca93654499ea3dafe":
            return "Kusama"
        case _:
            return { "ByGenesis": consensus_root.chainId }

for location in general_config["assets"]["assetsLocation"].values():
    chain_id = location["chainId"]

    consensus_root = get_consensus_root(chain_id)
    consensus_arg = construct_global_consensus_arg(consensus_root)

    location_items = list(location["multiLocation"].items())
    location_items.insert(0, ("globalConsensus", consensus_arg))
    location["multiLocation"] = dict(location_items)

write_data_to_file(config_files.general_config, json.dumps(general_config, indent=2))
