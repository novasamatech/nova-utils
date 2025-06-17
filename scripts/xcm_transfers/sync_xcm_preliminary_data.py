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
from scripts.xcm_transfers.utils.log import debug_log, enable_debug_log

config_files = get_xcm_config_files()

data = {}

def get_runtime_prefix(substrate: SubstrateInterface) -> str | None:
    registry = substrate.get_type_registry(substrate.block_hash)

    for type_name in registry:
        if type_name.endswith("RuntimeEvent"):
            return type_name.split("::")[0]

    return None

def get_xcm_outcome_type(substrate: SubstrateInterface) -> str | None:
    registry = substrate.get_type_registry(substrate.block_hash)

    for type_name in registry:
        if "xcm" in type_name and type_name.endswith("Outcome"):
            return type_name


def determine_dry_run_version(substrate: SubstrateInterface, runtime_prefix: str) -> int | None:
    try:
        # TODO we should migrate to inspecting v15 metadata which is ready at
        # https://github.com/polkascan/py-substrate-interface/pull/358/files
        # probably by forking the py-substrate-interface
        method_data = construct_v1_dry_run_method_data(substrate, runtime_prefix)
        substrate.rpc_request(method="state_call", params=["DryRunApi_dry_run_call", method_data])

        return dry_run_v1
    except SubstrateRequestException as e:
        error_message = e.args[0]["message"]

        if "DryRunApi_dry_run_xcm is not found" in error_message:
            return None
        # Dry run v2 has additional argument so it will result in a trap
        elif "Execution aborted due to trap" in error_message or "Client error: Execution failed: Execution aborted due to panic" in error_message:
            return dry_run_v2
        # Something unknown went wrong so we skip
        else:
            print("Unknown error:", e)

            return None

def construct_v1_dry_run_method_data(substrate: SubstrateInterface, runtime_prefix: str)-> str:
    origin_caller = substrate.encode_scale(f"{runtime_prefix}::OriginCaller", {"system": "Root"})
    call = substrate.compose_call(
        call_module="System",
        call_function="remark",
        call_params={
            "remark": "0x"
        }
    ).encode()
    method_data = origin_caller + call
    return method_data.to_hex()

def process_chain(idx, chain, len):
    print(f"\n{idx + 1}/{len}. Starting fetching data for {chain.name}")

    chain.create_connection()

    try:
        runtime_prefix = get_runtime_prefix(chain.substrate)
        if runtime_prefix is None:
            print(f"Runtime prefix in {chain.name} was not found, skipping")
            return
    except Exception as e:
        print(f"Failed to fetch runtime prefix for {chain.name} due to {e}, skipping")
        return

    try:
        xcm_outcome_type = get_xcm_outcome_type(chain.substrate)
        if xcm_outcome_type is None:
            print(f"Xcm outcome type in {chain.name} was not found, skipping")
            return
    except Exception as e:
        print(f"Failed to fetch xcm outcome type for {chain.name} due to {e}, skipping")
        return

    chain_dry_run_api_version = determine_dry_run_version(chain.substrate, runtime_prefix)
    print(f"{chain.name} dry run version: {chain_dry_run_api_version}")
    if chain_dry_run_api_version is None:
        return

    parachainId = None

    if chain.parentId is not None:
        try:
            parachainId = chain.substrate.query("ParachainInfo", "ParachainId").value
        except Exception as e:
            print(f"Failed to fetch ParachainId for {chain.name} due to {e}, skipping")
            return

    parachain_info = {
        "parachainId": parachainId,
        "runtimePrefix": runtime_prefix,
        "name": chain.name,
        "dryRunVersion": chain_dry_run_api_version,
        "xcmOutcomeType": xcm_outcome_type
    }
    data[chain.chainId] = parachain_info

    print(f"Finished fetching data for {chain.name}: {parachain_info}")
    write_data_to_file(config_files.xcm_additional_data, json.dumps(data, indent=4))


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
