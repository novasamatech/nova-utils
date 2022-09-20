import os
from tests.utils.getting_data import get_network_list
from tests.utils.chain_model import Chain

network_file_path = os.getenv('CHAINS_JSON_PATH', "/chains/v5/chains.json")
skipped_networks = ['Edgeware']

global chains

chains = [Chain(data) for data in get_network_list(
        network_file_path) if data.get('name') not in skipped_networks]
