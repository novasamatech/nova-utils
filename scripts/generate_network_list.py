#!/usr/bin/env python3


import json
import os
from jinja2 import Template
from pytablewriter import MarkdownTableWriter

from scripts.utils.chain_model import Chain

readme = Template("""
# Supported Networks & Assets data:
### 🕸️ Supported networks: {{ number_of_networks }}
### 💰 All assets {{ number_of_assets }}
### 🪙 Unique assets: {{ unique_assets }}
### 💫 Cross Chain directions: {{ number_of_xcms }}
### 🧾 SubQuery API projects: {{ number_of_subquery_explorers }}
### 👀 Networks with block explorers: {{ networks_with_block_explorers }}
---
{{networks_table}}
""")

CHAINS_VERSION = Chain.latest_config_version()
XCM_VERSION = os.getenv('XCM_VERSION')


def generate_networks_table():
    writer = MarkdownTableWriter(
        table_name="List of supported networks",
        headers=["--", "Network", "Assets", "Explorers", "SubQuery explorer"],
        value_matrix=generate_value_matrix(),
        margin=1
    )
    writer.write_table()
    return writer


def generate_value_matrix():
    returning_array = []
    with open(os.getcwd()+f"/chains/{CHAINS_VERSION}/chains.json", 'r') as json_file:
        data = json.load(json_file)
    for network in data:
        network_data_array = []
        network_data_array.append(network["name"])
        network_data_array.append(parse_parameters(
            "symbol", network.get("assets")))
        network_data_array.append(parse_parameters(
            "name", network.get("explorers")))
        network_data_array.append(parse_parameters(
            "history", network.get("externalApi")))
        returning_array.append(network_data_array)
    returning_array.sort()
    increment = iter(range(1, len(returning_array)+1))
    [network.insert(0, next(increment)) for network in returning_array]
    return returning_array


def parse_parameters(key_param, parsing_object):
    if parsing_object is None:
        return " - "

    if isinstance(parsing_object, dict):
        data = parsing_object.get(key_param, " - ")
        if isinstance(data, str):
            return data
        if isinstance(data, list):
            for item in data:
                if key_param == "history":
                    if item.get('type') == 'subquery':
                        return item.get('url')
                    if item.get('type') == 'etherscan':
                        return item.get('url')
                    return ", ".join(data)
                else:
                    raise Exception(F"Unknown key_param: {key_param}")

    if key_param == "symbol":
        return '<br />'.join(str(x.get(key_param)) for x in parsing_object)
    else:
        return_data = '<br />'.join(str(x.get(key_param))
                                    for x in parsing_object)

    if return_data is None:
        return " - "
    return return_data


def calculate_parameters(list_of_arrays, element_name):
    unique_elements = []
    all_elements = []
    element_index = 0
    for index, header in enumerate(list_of_arrays.headers):
        if header == element_name:
            element_index = index
            break

    for value in list_of_arrays.value_matrix:
        if value[element_index] == " - ":
            continue
        if element_name == "Network":
            all_elements.append(value[element_index])
            if value[element_index] not in unique_elements:
                unique_elements.append(value[element_index])
        elif element_name == "Assets":
            asset_list = value[element_index].split('<br />')
            for asset in asset_list:
                all_elements.append(value[element_index])
                if asset not in unique_elements:
                    unique_elements.append(asset)
        elif element_name == "SubQuery explorer":
            all_elements.append(value[element_index])
            if value[element_index] not in unique_elements:
                unique_elements.append(value[element_index])
        elif element_name == "Explorers":
            all_elements.append(value[element_index])
            if value[element_index] not in unique_elements:
                unique_elements.append(value[element_index])
        else:
            raise Exception("Unknown type of value")

    return len(unique_elements), len(all_elements)


def calculate_number_of_xcms():
    with open(os.getcwd()+f"/xcm/{XCM_VERSION}/transfers.json", 'r') as json_file:
        transfers_data = json.load(json_file)
        accumulator = 0
        for network in transfers_data.get('chains'):
            for asset in network.get('assets'):
                accumulator += len(asset.get('xcmTransfers', []))
    with open(os.getcwd()+f"/xcm/{XCM_VERSION}/transfers_dynamic.json", 'r') as json_file:
        dynamic_transfers_data = json.load(json_file)
        for network in dynamic_transfers_data.get('chains'):
            for asset in network.get('assets'):
                accumulator += len(asset.get('xcmTransfers', []))
    return accumulator



if __name__ == '__main__':
    with open("./chains/README.md", "w") as f:
        network_table = generate_networks_table()
        unique_networks, all_networks = calculate_parameters(
            network_table, 'Network')
        uniques_assets, all_assets = calculate_parameters(
            network_table, 'Assets')
        unique_sq_explorers, all_explorers = calculate_parameters(
            network_table, 'SubQuery explorer')
        unique_explorers, all_explorers = calculate_parameters(
            network_table, 'Explorers')
        xcm_number = calculate_number_of_xcms()
        f.write(readme.render(
            networks_table=network_table,
            number_of_networks=unique_networks,
            number_of_assets=all_assets,
            number_of_subquery_explorers=unique_sq_explorers,
            networks_with_block_explorers=all_explorers,
            unique_assets=uniques_assets,
            number_of_xcms=xcm_number
        ))
