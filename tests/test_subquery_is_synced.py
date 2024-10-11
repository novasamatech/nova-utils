import requests
import pytest
from typing import List
from scripts.utils.work_with_data import get_network_list

payload = "{\"query\":\"query{\\n  _metadata{\\n    chain\\n    lastProcessedHeight\\n    targetHeight\\n  }\\n}\",\"variables\":{}}"
headers = {
    'Host': 'gateway.subquery.network',
    'Connection': 'Keep-Alive',
    'User-Agent': 'okhttp/4.11.0',
    'Content-Type': 'application/json; charset=UTF-8'
}


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


@pytest.fixture(scope="module")
def subquery_projects():
    network_file_path = "chains/v20/chains.json"
    network_list = get_network_list('/' + network_file_path)
    return get_unique_subquery_urls(network_list)


def test_subquery_is_synced(subquery_projects):
    for url in subquery_projects:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            last_processed_height = response.json().get('data').get('_metadata').get('lastProcessedHeight')
            target_height = response.json().get('data').get('_metadata').get('targetHeight')
            assert abs(target_height - last_processed_height) < 10
