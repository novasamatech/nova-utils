from __future__ import annotations

import json

from substrateinterface import SubstrateInterface

from scripts.utils.chain_model import Chain
from utils.work_with_data import get_data_from_file, write_data_to_file

chains_file = get_data_from_file("../chains/v21/chains_dev.json")

chains = [Chain(it) for it in chains_file]

polkadot_id = "91b171bb158e2d3848fa23a9f1c25182fb8e20313b2c1eb49219da7a70ce90c3"

polkadot = next((chain for chain in chains if chain.chainId == polkadot_id))
polkadot_parachains = [chain for chain in chains if chain.parentId == polkadot_id]

polkadot_chains = [polkadot] + polkadot_parachains

data = {}


def get_runtime_prefix(substrate: SubstrateInterface) -> str | None:
    registry = substrate.get_type_registry(substrate.block_hash)

    for type_name in registry:
        if type_name.endswith("RuntimeEvent"):
            return type_name.split("::")[0]

    return None


for idx, chain in enumerate(polkadot_chains):
    print(f"\n{idx+1}/{len(polkadot_parachains)}. Starting fetching data for {chain.name}")

    parachainId = None

    if chain.parentId is not None:
        try:
            parachainId = chain.access_substrate(lambda s: s.query("ParachainInfo", "ParachainId").value)
        except Exception as e:
            print(f"Failed to fetch ParachainId for {chain.name} due to {e}, skipping")
            continue

    try:
        runtime_prefix = chain.access_substrate(lambda s: get_runtime_prefix(s))
        if runtime_prefix is None:
            print(f"Runtime prefix in {chain.name} was not found, skipping")
    except Exception as e:
        print(f"Failed to fetch runtime prefix for {chain.name} due to {e}, skipping")
        continue

    parachain_info = {"parachainId": parachainId, "runtimePrefix": runtime_prefix}
    data[chain.chainId] = parachain_info

    print(f"Finished fetching data for {chain.name}: {parachain_info}")
    write_data_to_file('xcm_additional_data.json', json.dumps(data, indent=4))