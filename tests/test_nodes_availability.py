
from typing import List
import pytest

from substrateinterface import SubstrateInterface
from tests.data.setting_data import chains
from scripts.utils.substrate_interface import create_connection_by_url
from scripts.utils.chain_model import Chain


def collect_nodes_for_chains(networks: List[Chain]):
    result = []
    for network in networks:
        for node in network.nodes:
            result.append(
                {"url": node.get("url"), "name": network.name})

    return result

task_ids = [
    f'Test for {task["name"]}, url: {task["url"]}'
    for task in collect_nodes_for_chains(chains)
]


@pytest.mark.parametrize("data", collect_nodes_for_chains(chains), ids=task_ids)
def test_can_create_connection(data):

    connectin = create_connection_by_url(data["url"])
    assert isinstance(connectin, SubstrateInterface)
