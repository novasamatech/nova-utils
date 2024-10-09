import requests
import pytest

subquery_urls = [
    ["Khala", "https://gateway.subquery.network/query/0x3a"],
    ["Kilt", "https://gateway.subquery.network/query/0x3d"],
    ["Calamari", "https://gateway.subquery.network/query/0x36"],
    ["Quartz", "https://gateway.subquery.network/query/0x3e"],
    ["Bit.country", "https://gateway.subquery.network/query/0x41"],
    ["Acala", "https://gateway.subquery.network/query/0x3c"],
    ["PAH", "https://gateway.subquery.network/query/0x35"],
    ["Picasso", "https://gateway.subquery.network/query/0x3b"],
    ["Polkadex", "https://gateway.subquery.network/query/0x20"],
    ["Shiden", "https://gateway.subquery.network/query/0x40"],
    ["Bifrost", "https://gateway.subquery.network/query/0x38"],
    ["Basilisk", "https://gateway.subquery.network/query/0x3f"],
    ["Altair", "https://gateway.subquery.network/query/0x37"],
    ["Karura", "https://gateway.subquery.network/query/0x39"]
]

payload = "{\"query\":\"query{\\n  _metadata{\\n    chain\\n    lastProcessedHeight\\n    targetHeight\\n  }\\n}\",\"variables\":{}}"
headers = {
    'Host': 'gateway.subquery.network',
    'Connection': 'Keep-Alive',
    'User-Agent': 'okhttp/4.11.0',
    'Content-Type': 'application/json; charset=UTF-8'
}


@pytest.mark.parametrize("chain, url", subquery_urls)
def test_subquery_status_code_equals_200(chain, url):
    response = requests.request("POST", url, headers=headers, data=payload)
    assert response.status_code == 200, f"Test failed for chain: {chain}"


@pytest.mark.parametrize("chain, url", subquery_urls)
def test_response_has_data(chain, url):
    response = requests.request("POST", url, headers=headers, data=payload)
    assert response.json().get('data'), f"Test failed for chain: {chain}"


@pytest.mark.parametrize("chain, url", subquery_urls)
def test_data_has_metadata(chain, url):
    response = requests.request("POST", url, headers=headers, data=payload)
    assert response.json().get('data').get('_metadata'), f"Test failed for chain: {chain}"


@pytest.mark.parametrize("chain, url", subquery_urls)
def test_metadata_has_last_processed_height(chain, url):
    response = requests.request("POST", url, headers=headers, data=payload)
    last_processed_height = response.json().get('data').get('_metadata').get('lastProcessedHeight')
    assert isinstance(last_processed_height, int), f"Test failed for chain: {chain}"


@pytest.mark.parametrize("chain, url", subquery_urls)
def test_metadata_has_target_height(chain, url):
    response = requests.request("POST", url, headers=headers, data=payload)
    target_height = response.json().get('data').get('_metadata').get('targetHeight')
    assert isinstance(target_height, int), f"Test failed for chain: {chain}"


@pytest.mark.parametrize("chain, url", subquery_urls)
def test_target_and_last_processed_height_diff(chain, url):
    response = requests.request("POST", url, headers=headers, data=payload)
    last_processed_height = response.json().get('data').get('_metadata').get('lastProcessedHeight')
    target_height = response.json().get('data').get('_metadata').get('targetHeight')
    assert abs(target_height - last_processed_height) < 10, f"Test failed for chain: {chain}"


@pytest.mark.parametrize("chain, url", subquery_urls)
def test_metadata_has_chain(chain, url):
    response = requests.request("POST", url, headers=headers, data=payload)
    chain = response.json().get('data').get('_metadata').get('chain')
    assert isinstance(chain, str), f"Test failed for chain: {chain}"
