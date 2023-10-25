import pytest

from substrateinterface import SubstrateInterface
from scripts.utils.chain_model import Chain
from scripts.utils.metadata_interaction import get_properties
from scripts.utils.substrate_interface import create_connection_by_url
from tests.data.setting_data import collect_nodes_for_chains, get_substrate_chains


chain_names = [
    f'Test for {task.name}'
    for task in get_substrate_chains()
]

task_ids = [
    f'Test for {task["name"]}, url: {task["url"]}'
    for task in collect_nodes_for_chains(get_substrate_chains())
]

@pytest.fixture(scope="module", params=collect_nodes_for_chains(get_substrate_chains()), ids=task_ids)
def connection_by_url(request):
    data = request.param
    connection = create_connection_by_url(data["url"])
    get_properties(connection)
    return connection

@pytest.fixture(scope="module", params=get_substrate_chains(), ids=chain_names)
def chain_model(request) -> Chain:
    chain = request.param
    chain.create_connection()
    chain.init_properties()
    return chain
