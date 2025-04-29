import functools
from typing import Tuple, List

from scalecodec import ScaleBytes

from scripts.utils.chain_model import Chain
from scripts.utils.work_with_data import get_data_from_file
from scripts.xcm_transfers.utils.dry_run_api_types import dry_run_api_types
from scripts.xcm_transfers.utils.log import debug_log
from scripts.xcm_transfers.utils.xcm_config_files import XCMConfigFiles
from scripts.xcm_transfers.xcm.multi_location import GlobalMultiLocation
from scripts.xcm_transfers.xcm.registry.reserve_location import ReserveLocation, ReserveLocations
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.registry.xcm_registry import XcmRegistry


def _map_junction_from_config(config_key: str, config_value) -> dict:
    match config_key:
        case "parachainId":
            return {"Parachain": config_value}
        case "generalKey":
            return {"GeneralKey": _general_key_junction(config_value)}
        case "generalIndex":
            return {"GeneralIndex": int(config_value)}
        case "palletInstance":
            return {"PalletInstance": config_value}


def _truncate_or_pad(data: bytes, required_size: int) -> bytes:
    truncated = data[0::required_size]
    padded = truncated.rjust(required_size, b'\0')
    return bytes(padded)


def _general_key_junction(key) -> dict:
    scale_bytes = ScaleBytes(key)

    fixed_size_bytes = _truncate_or_pad(scale_bytes.data, required_size=32)

    return {"length": scale_bytes.length, "data": fixed_size_bytes}


def _build_reserve_locations_map(
        asset_locations_config: dict,
        xcm_registry: XcmRegistry
) -> dict[str, ReserveLocation]:
    result = {}

    for reserve_id, reserve_config in asset_locations_config.items():
        junctions = [_map_junction_from_config(config_key, config_value) for config_key, config_value in
                     reserve_config["multiLocation"].items()]

        chain_id = reserve_config["chainId"]

        global_location = GlobalMultiLocation(junctions)

        result[reserve_id] = ReserveLocation(chain_id, global_location, xcm_registry.get_chain)

    return result


def _build_reserve_overrides(reserve_id_overrides: dict) -> dict[Tuple[str, int], str]:
    result = {}

    for chain_id, chain_reserve_overrides in reserve_id_overrides.items():
        for asset_id, reserve_id in chain_reserve_overrides.items():
            result[(chain_id, int(asset_id))] = reserve_id

    return result


def _build_reserves(xcm_config: dict, xcm_registry: XcmRegistry) -> ReserveLocations:
    reserve_locations = _build_reserve_locations_map(xcm_config["assetsLocation"], xcm_registry)
    asset_reserve_overrides = _build_reserve_overrides(xcm_config.get("reserveIdOverrides"))

    return ReserveLocations(reserve_locations, asset_reserve_overrides)

def build_xcm_registry(files: XCMConfigFiles) -> XcmRegistry:
    all_xcm_capable_chains = build_all_xcm_capable_chains(files)
    xcm_config = get_data_from_file(files.xcm_dynamic_config)

    return XcmRegistry(all_xcm_capable_chains, functools.partial(_build_reserves, xcm_config))

def build_all_xcm_capable_chains(files: XCMConfigFiles) -> List[XcmChain]:
    additional_xcm_data = get_data_from_file(files.xcm_additional_data)
    chains_file = get_data_from_file(files.chains)

    result = []

    for chain_config in chains_file:
        additional_xcm_chain_data = additional_xcm_data.get(chain_config["chainId"], None)

        if additional_xcm_chain_data is None:
            debug_log(f"No additional xcm data found for {chain_config['name']}, skipping")
            continue

        runtime_prefix = additional_xcm_chain_data["runtimePrefix"]
        dry_run_version = additional_xcm_chain_data["dryRunVersion"]
        xcm_outcome_type = additional_xcm_chain_data["xcmOutcomeType"]
        type_registry = dry_run_api_types(runtime_prefix, dry_run_version, xcm_outcome_type)

        chain = Chain(chain_config, type_registry)

        parachain_id = additional_xcm_chain_data["parachainId"]
        xcm_chain = XcmChain(chain, parachain_id)
        result.append(xcm_chain)

    return result
