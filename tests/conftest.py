import pytest

from func_timeout import func_timeout, FunctionTimedOut
from scripts.utils.chain_model import Chain
from scripts.utils.metadata_interaction import get_properties
from scripts.utils.substrate_interface import create_connection_by_url
from tests.data.setting_data import collect_nodes_for_chains, get_substrate_chains

FIXTURE_TIMEOUT = 10

chain_names = [
    f'Test for {task.name}'
    for task in get_substrate_chains()
]

task_ids = [
    f'Test for {task["name"]}, url: {task["url"]}'
    for task in collect_nodes_for_chains(get_substrate_chains())
]
def execute_with_timeout(timeout: int, function: function, args: tuple, error_message: str):
    try:
        return func_timeout(timeout=timeout, func=function, args=args)
    except FunctionTimedOut:
        pytest.fail(msg=error_message)

@pytest.fixture(scope="module", params=collect_nodes_for_chains(get_substrate_chains()), ids=task_ids)
def connection_by_url(request):
    data = request.param
    connection = execute_with_timeout(
        timeout=FIXTURE_TIMEOUT,
        function=create_connection_by_url,
        args=(data["url"],),
        error_message=f'Timeout {FIXTURE_TIMEOUT} when creating connection: {data["url"]}'
    )
    execute_with_timeout(
        timeout=FIXTURE_TIMEOUT,
        function=get_properties,
        args=(connection,),
        error_message=f'Timeout {FIXTURE_TIMEOUT} when getting properties: {data["url"]}'
    )
    return connection

@pytest.fixture(scope="module", params=get_substrate_chains(), ids=chain_names)
def chain_model(request) -> Chain:
    chain = request.param
    execute_with_timeout(
        timeout=FIXTURE_TIMEOUT,
        function=chain.create_connection,
        args=(),
        error_message=f'Timeout {FIXTURE_TIMEOUT} when creating connection: {chain.name}'
    )
    execute_with_timeout(
        timeout=FIXTURE_TIMEOUT,
        function=chain.init_properties,
        args=(),
        error_message=f'Timeout {FIXTURE_TIMEOUT} when initializing properties: {chain.name}'
    )
    return chain
