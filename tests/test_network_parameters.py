import json
import pytest
from scripts.create_type_file import get_properties, create_connection_by_url

with open("../chains/v3/chains.json") as fin:
    chains_data = json.load(fin)

test_data = []
for chain in chains_data:
    data = (chain['nodes'][0]['url'], chain['assets'][0]['precision'], chain['addressPrefix'], chain['chainId'])
    test_data.append(data)


@pytest.mark.parametrize("url, expected_precision, expected_address_format, expected_genesis", test_data)
def test_properties(url, expected_precision, expected_address_format, expected_genesis):
    network_property = get_properties(create_connection_by_url(url))
    if isinstance(network_property.precision, list):
        assert network_property.precision[0] == expected_precision
    else:
        assert network_property.precision == expected_precision
    assert network_property.ss58Format == expected_address_format
    assert network_property.chainId[2:] == expected_genesis
