import os
import json

from typing import List
from scripts.utils.work_with_data import get_network_list
from scripts.utils.chain_model import Chain

network_file_path = os.getenv('CHAINS_JSON_PATH', "chains/v18/chains.json")
xcm_file_path = os.getenv('DEV_XCM_JSON_PATH', "xcm/v6/transfers_dev.json")
skipped_networks = ['Edgeware']
network_list = get_network_list('/' + network_file_path)


def get_substrate_chains() -> list[Chain]:
    substrate_chains: list[Chain] = []
    for data in network_list:
        if data.get('name') in skipped_networks or 'PAUSED' in data.get('name'):
            continue
        options = data.get('options')

        if options is None:
            substrate_chains.append(Chain(data))
        elif 'noSubstrateRuntime' not in options:
            substrate_chains.append(Chain(data))
        else:
            continue

    return substrate_chains


def load_xcm_data():
    with open(xcm_file_path) as f:
        return json.load(f)


def get_parachains() -> List[Chain]:
    substrate_chains = get_substrate_chains()
    parachains = [chain for chain in substrate_chains if chain.is_parachain()]
    return parachains


def get_relaychains() -> List[Chain]:
    substrate_chains = get_substrate_chains()
    relaychains = [
        chain for chain in substrate_chains if not chain.is_parachain()]
    return relaychains


def get_parachains_with_xcm() -> List[Chain]:
    substrate_parachains = get_parachains()
    xcm_data = load_xcm_data()
    chain_ids = [chain['chainId'] for chain in xcm_data['chains']]
    parachains_with_xcm = [
        chain for chain in substrate_parachains if chain.chainId in chain_ids]

    return parachains_with_xcm


def get_relaychains_with_xcm() -> List[Chain]:
    substrate_relaychains = get_relaychains()
    xcm_data = load_xcm_data()
    chain_ids = [chain['chainId'] for chain in xcm_data['chains']]
    relaychains_with_xcm = [
        chain for chain in substrate_relaychains if chain.chainId in chain_ids]

    return relaychains_with_xcm


def get_ethereum_chain():
    eth_chains = []
    for data in network_list:
        if data.get('chainId') == 'eip155:1':
            eth_chains.append(Chain(data))

    return eth_chains


def collect_nodes_for_chains(networks: List[Chain]):
    result = []
    for network in networks:
        for node in network.nodes:
            result.append(
                {"url": node.get("url"), "name": network.name})

    return result


def collect_rpc_nodes_for_chains(networks: List[Chain]):
    result = []
    for network in networks:
        for node in network.nodes:
            if 'https' in node.get("url"):
                result.append(
                    {"url": node.get("url"), "name": network.name}
                )

    return result
