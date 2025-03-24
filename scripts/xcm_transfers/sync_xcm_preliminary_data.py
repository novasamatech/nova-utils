from __future__ import annotations

import json
from typing import List

from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

from scripts.utils.chain_model import Chain
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.utils.chain_ids import RELAYS

data = {}

def get_runtime_prefix(substrate: SubstrateInterface) -> str | None:
    registry = substrate.get_type_registry(substrate.block_hash)

    for type_name in registry:
        if type_name.endswith("RuntimeEvent"):
            return type_name.split("::")[0]

    return None


def chain_has_dry_run_api(substrate: SubstrateInterface) -> bool:
    try:
        substrate.rpc_request(method="state_call", params=["DryRunApi_dry_run_xcm", "0x"])
    except SubstrateRequestException as e:
        return "DryRunApi_dry_run_xcm is not found" not in e.args[0]["message"]

    # We don't form a valid dry run params so successfully execution should not be possible but still return True in
    # case it somehow happened
    return True


def process_chain(idx, chain, len):
    print(f"\n{idx + 1}/{len}. Starting fetching data for {chain.name}")

    chain.create_connection()

    if not chain_has_dry_run_api(chain.substrate):
        print(f"{chain.name} does not yet have dry run Api, skipping")

        return

    parachainId = None

    if chain.parentId is not None:
        try:
            parachainId = chain.substrate.query("ParachainInfo", "ParachainId").value
        except Exception as e:
            print(f"Failed to fetch ParachainId for {chain.name} due to {e}, skipping")
            return

    try:
        runtime_prefix = get_runtime_prefix(chain.substrate)
        if runtime_prefix is None:
            print(f"Runtime prefix in {chain.name} was not found, skipping")
    except Exception as e:
        print(f"Failed to fetch runtime prefix for {chain.name} due to {e}, skipping")
        return

    parachain_info = {"parachainId": parachainId, "runtimePrefix": runtime_prefix, "name": chain.name}
    data[chain.chainId] = parachain_info

    print(f"Finished fetching data for {chain.name}: {parachain_info}")
    write_data_to_file('xcm_registry_additional_data.json', json.dumps(data, indent=4))


def find_xcm_chains(chains: List[Chain], relay_ids: list[str] = RELAYS) -> List[Chain]:
    result = []

    for relay_id in relay_ids:
        relay = next((chain for chain in chains if chain.chainId == relay_id), None)
        if relay is None:
            continue

        parachains = [chain for chain in chains if chain.parentId == relay_id]
        if len(parachains) == 0:
            continue

        result.extend([relay] + parachains)

    return result

chains_file = get_data_from_file("../../chains/v21/chains_dev.json")
chains = [Chain(it) for it in chains_file]

xcm_chains = find_xcm_chains(chains)

for idx, chain in enumerate(xcm_chains):
    try:
        process_chain(idx, chain, len(xcm_chains))
    except Exception as e:
        print(f"Error happened when processing {chain.name}, skipping: {e}")

        continue

