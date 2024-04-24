import os
import pytest
from scripts.create_type_file import create_connection_by_url
from tests.test_network_parameters import get_network_list
from tests.utils.chain_model import Chain
from substrateinterface import SubstrateInterface


def collect_nodes_from_dev():
    networks = []
    for network in get_network_list(network_file_path):
        current_network = Chain(network)
        for node in current_network.nodes:
            networks.append(node.get("url"))

    return networks

network_file_path=os.environ['JSON_PATH']

@pytest.mark.parametrize("url", collect_nodes_from_dev())
def test_can_create_connection(url):

    connectin = create_connection_by_url(url)
    assert isinstance(connectin, SubstrateInterface)
