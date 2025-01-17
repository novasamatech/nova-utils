import os
import allure
import pytest

from typing import List
from scripts.utils.work_with_data import get_network_list
from func_timeout import func_timeout, FunctionTimedOut
from scripts.utils.chain_model import Chain
from scripts.utils.metadata_interaction import get_properties
from scripts.utils.substrate_interface import create_connection_by_url
from tests.data.setting_data import collect_nodes_for_chains, get_substrate_chains

FIXTURE_TIMEOUT = 15

chain_names = [
    f'Test for {task.name}'
    for task in get_substrate_chains()
]

task_ids = [
    f'Test for {task["name"]}, url: {task["url"]}'
    for task in collect_nodes_for_chains(get_substrate_chains())
]


class FixtureTimeoutError(Exception):
    pass


def execute_with_timeout(timeout: int, function, args: tuple, error_message: str):
    try:
        return func_timeout(timeout=timeout, func=function, args=args)
    except FunctionTimedOut:
        with allure.step("Function timed out"):
            allure.attach(name="Error", body=error_message,
                          attachment_type=allure.attachment_type.TEXT)
        raise FixtureTimeoutError(error_message)


def get_unique_subquery_urls(network_list: List[dict]) -> List[str]:
    subquery_urls = set()
    for chain in network_list:
        external_api = chain.get('externalApi', {})
        for api_type, api_list in external_api.items():
            if isinstance(api_list, list):
                for api in api_list:
                    if api.get('type') == 'subquery':
                        subquery_urls.add(api['url'])
            elif isinstance(api_list, dict) and api_list.get('type') == 'subquery':
                subquery_urls.add(api_list['url'])
    return list(subquery_urls)


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


@pytest.fixture(scope="module")
def subquery_projects():
    network_file_path = os.getenv('CHAINS_JSON_PATH', "chains/v21/chains.json")
    network_list = get_network_list('/' + network_file_path)
    return get_unique_subquery_urls(network_list)
