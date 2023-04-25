
import pytest

from substrateinterface import SubstrateInterface
from tests.data.setting_data import get_substrate_chains, collect_nodes_for_chains
from scripts.utils.substrate_interface import create_connection_by_url


task_ids = [
    f'Test for {task["name"]}, url: {task["url"]}'
    for task in collect_nodes_for_chains(get_substrate_chains())
]


@pytest.mark.parametrize("data", collect_nodes_for_chains(get_substrate_chains()), ids=task_ids)
def test_can_create_connection(data):

    connectin = create_connection_by_url(data["url"])
    assert isinstance(connectin, SubstrateInterface)
