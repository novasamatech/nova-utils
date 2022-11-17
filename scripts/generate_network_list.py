#!/usr/bin/env python3


import json
import os
from jinja2 import Template
from pytablewriter import MarkdownTableWriter


readme = Template("""
# Some brief data about supported networks:
### 🕸️ Supported networks: {{ number_of_networks }}
### 🪙 Unique assets: {{ number_of_assets }}
### 🧾 Subquery projects: {{ number_of_subquery_explorers }}
### 👀 Networks without any block explorers: {{ number_of_networks_without_explorers }}
---
{{networks_table}}
""")

CHAINS_VERSION = os.getenv('CHAINS_VERSION', default = "v6")


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
                        return subquery_url_formator(item.get('url'))
                    return ", ".join(data)
                else:
                    raise Exception(F"Unknown key_param: {key_param}")

    if key_param == "symbol":
        return '<br />'.join(str(x.get(key_param)) for x in parsing_object)
    else:
        return_data = '<br />'.join(str(x.get(key_param)) for x in parsing_object)

    if return_data is None:
        return " - "
    return return_data


def subquery_url_formator(url):
    explorer_base_url = "https://explorer.subquery.network/subquery/nova-wallet/"

    if "gapi" in url:
        organisation = "nova-"
        injecting_part = url.split("-")[1].split(".")[0]
        final_explorer_url = f"[{organisation+injecting_part}]({explorer_base_url + organisation + injecting_part})"
        return final_explorer_url
    else:
        injecting_part = url.split("/")[-1]
        final_explorer_url = f"[{injecting_part}]({explorer_base_url + injecting_part})"
        return final_explorer_url

def calculate_unique_elements(list_of_arrays, element_name):
    unique_elements = []
    element_index = 0
    for index, header in enumerate(list_of_arrays.headers):
        if header == element_name:
            element_index = index
            break

    for value in list_of_arrays.value_matrix:
        if element_name == "Network":
            if value[element_index] not in unique_elements:
                unique_elements.append(value[element_index])
        elif element_name == "Assets":
            asset_list = value[element_index].split('<br />')
            for asset in asset_list:
                if asset not in unique_elements:
                    unique_elements.append(asset)
        elif element_name == "SubQuery explorer":
            if value[element_index] != " - ":
                if value[element_index] not in unique_elements:
                    unique_elements.append(value[element_index])
        elif element_name == "Explorers": # There is value not unique
            if value[element_index] != " - ":
                unique_elements.append(value[element_index])
        else:
            raise Exception("Unknown type of value")

    return len(unique_elements)

if __name__ == '__main__':

    with open("./chains/README.md", "w") as f:
        network_table = generate_networks_table()
        networks_numer = calculate_unique_elements(network_table, 'Network')
        number_of_assets = calculate_unique_elements(network_table, 'Assets')
        number_of_subquery_explorers = calculate_unique_elements(network_table, 'SubQuery explorer')
        number_of_networks_without_explorers = networks_numer - calculate_unique_elements(network_table, 'Explorers')
        f.write(readme.render(
            networks_table=network_table,
            number_of_networks=networks_numer,
            number_of_assets=number_of_assets,
            number_of_subquery_explorers=number_of_subquery_explorers,
            number_of_networks_without_explorers=number_of_networks_without_explorers
        ))
