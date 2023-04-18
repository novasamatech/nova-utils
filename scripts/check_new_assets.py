#!/usr/bin/env python3

import json
import os
import pytest
from scripts.generate_network_list import parse_parameters
from scripts.utils.substrate_interface import create_connection_by_url
from scripts.create_type_file import get_properties

CHAINS_VERSION = os.getenv('CHAINS_VERSION')


def generate_test_data():
    returning_array = []
    with open(os.getcwd() + f"/chains/{CHAINS_VERSION}/chains.json", 'r') as json_file:
        data = json.load(json_file)
    for network in data:
        network_data_array = []
        network_data_array.append(parse_parameters(
            "symbol", network.get("assets")))
        network_data_array.append(network["nodes"][0]["url"])
        returning_array.append(network_data_array)
    returning_array.sort()
    return returning_array


test_data = generate_test_data()


@pytest.mark.parametrize("expected, url", test_data)
def test_properties(url, expected):
    network_property = get_properties(create_connection_by_url(url))
    assert network_property.assets == expected
