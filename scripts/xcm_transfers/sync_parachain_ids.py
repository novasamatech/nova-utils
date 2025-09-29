from __future__ import annotations

import json
from typing import List

from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

from scripts.utils.chain_model import Chain
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.config_setup import get_xcm_config_files
from scripts.xcm_transfers.utils.chain_ids import RELAYS
from scripts.xcm_transfers.utils.dry_run_api_types import dry_run_v1, dry_run_v2

config_files = get_xcm_config_files()
general_config = get_data_from_file(config_files.general_config)

data = {}

def process_chain(idx, chain, len):
    print(f"\n{idx + 1}/{len}. {chain.name}")

    chain.create_connection()

    parachainId = None

    if chain.parentId is not None:
        try:
            parachainId = chain.substrate.query("ParachainInfo", "ParachainId").value
        except Exception as e:
            print(f"Failed to fetch ParachainId for {chain.name} due to {e}, skipping")
            return

    if parachainId is not None:
        data[chain.chainId] = parachainId
        save_synced_data()

    print(f"{chain.name}: {parachainId}")

def save_synced_data():
    general_config["chains"]["parachainIds"] = data

    write_data_to_file(config_files.general_config, json.dumps(general_config, indent=2))


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

chains_file = get_data_from_file(config_files.chains)
chains = [Chain(it) for it in chains_file]

xcm_chains = find_xcm_chains(chains)

for idx, chain in enumerate(xcm_chains):
    try:
        process_chain(idx, chain, len(xcm_chains))
    except Exception as e:
        print(f"Error happened when processing {chain.name}, skipping: {e}")

        continue
