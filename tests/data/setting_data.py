import os
from scripts.utils.work_with_data import get_network_list
from scripts.utils.chain_model import Chain

network_file_path = os.getenv('CHAINS_JSON_PATH', "chains/v10/chains.json")
skipped_networks = ['Edgeware', 'Ethereum']

global chains

chains = [Chain(data) for data in get_network_list('/'+
        network_file_path) if data.get('name') not in skipped_networks]
