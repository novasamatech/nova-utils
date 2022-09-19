import os
import pytest
from tests.utils.getting_data import get_network_list
from tests.utils.chain_model import Chain


def collect_data_from_dev():
    chains = []
    for network in get_network_list(network_file_path):
        current_network = Chain(network)
        chains.append(current_network)

    return chains

network_file_path=os.getenv('JSON_PATH', "/chains/v5/chains_dev.json")

chains = (
    collect_data_from_dev()
)

task_ids = [
    f'Test for {task.name}'
    for task in chains
]


@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestChainJson:

    def test_address_prefix(self, chain: Chain):
        chain.create_connection()
        chain.init_properties()
        assert chain.properties.ss58Format == chain.addressPrefix

    def test_chainId(self, chain: Chain):
        chain.create_connection()
        chain.init_properties()
        assert chain.properties.chainId == '0x'+chain.chainId

    def test_precision(self, chain: Chain):
        chain.create_connection()
        chain.init_properties()
        assert chain.properties.precision == chain.assets[0].get('precision')
