import pytest

from func_timeout import func_timeout, FunctionTimedOut
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
    timeout = 10
    data = request.param
    try:
        connection = func_timeout(timeout, create_connection_by_url, args=(data["url"],))
        func_timeout(timeout, get_properties, args=(connection,))
        return connection
    except FunctionTimedOut:
        pytest.fail(f'Reach timeout {timeout} for create connection on: {data["url"]}')

@pytest.fixture(scope="module", params=get_substrate_chains(), ids=chain_names)
def chain_model(request) -> Chain:
    chain = request.param
    chain.create_connection()
    chain.init_properties()
    return chain
