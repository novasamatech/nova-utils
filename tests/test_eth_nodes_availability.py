import os
import pytest
import time
from urllib.parse import urlparse
from web3 import Web3

from tests.data.setting_data import collect_rpc_nodes_for_chains, get_ethereum_chain

# The nodes the tested ones are compared with, in order of preference. They must be keyless: this
# repository is public. A tested node is never compared with a reference of its own provider.
REFERENCE_ETH_WSS_NODES = os.environ.get(
    'REFERENCE_ETH_WSS_NODES', 'wss://ethereum-rpc.publicnode.com,wss://0xrpc.io/eth'
).split(',')


def reference_node_for(url):
    host = urlparse(url).hostname
    return next(node for node in REFERENCE_ETH_WSS_NODES if urlparse(node).hostname != host)


task_ids = [
    f'Test for {task["name"]}, url: {task["url"]}'
    for task in collect_rpc_nodes_for_chains(get_ethereum_chain())
]

@pytest.mark.parametrize("data", collect_rpc_nodes_for_chains(get_ethereum_chain()), ids=task_ids)
class TestETHNodesAvailability:
    def test_rpc_node_work_fast(self, data):

        w3 = Web3(Web3.HTTPProvider(data['url']))
        # Check if connected to Ethereum RPC node
        assert w3.is_connected(), "Failed to connect to Ethereum RPC node"

        # Measure time taken to retrieve current block
        start_time = time.time()
        w3.eth.get_block('latest')
        end_time = time.time()

        # Check if request took more than 3 seconds
        elapsed_time = end_time - start_time
        assert elapsed_time <= 3, f"Request took {elapsed_time} seconds, which is more than 3 seconds"

    def test_rpc_node_is_synced(self, data):

        wss_w3 = Web3(Web3.WebsocketProvider(reference_node_for(data['url'])))
        # Check if connected to wss node
        assert wss_w3.is_connected(), "Failed to connect to Ethereum wss node"

        w3_rpc = Web3(Web3.HTTPProvider(data['url']))
        # Check if connected to RPC node
        assert w3_rpc.is_connected(), "Failed to connect to Ethereum RPC node"

        # Get the latest block number from nodes
        rpc_block_number = w3_rpc.eth.block_number
        wss_block_number = wss_w3.eth.block_number

        # Compare block numbers and assert the difference is not greater than 3
        assert abs(wss_block_number - rpc_block_number) <= 3, f"Difference in block numbers is greater than 3:\
            wss_block_number={wss_block_number}, rpc_block_number={rpc_block_number}"
