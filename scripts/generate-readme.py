#!/usr/bin/env python3


import json
import os
from jinja2 import Template
from pytablewriter import MarkdownTableWriter


readme = Template("""
{{networks_table}}
""")

CHAINS_VERSION = "v3"

def generate_networks_table():
    writer = MarkdownTableWriter(
        table_name="List of supported networks",
        headers=["Network", "Assets", "Explorers", "History", "Staking"],
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
        network_data_array.append(parse_parameters(
            "staking", network.get("externalApi")))
        returning_array.append(network_data_array)
    return returning_array


def parse_parameters(key_param, object):
    if object is None:
        return " - "

    if type(object) is dict:
        data = object.get(key_param, " - ")
        if type(data) is str:
            return data
        return "[{name}]({link})".format(name=data.get("type"), link=data.get("url"))

    return_data = '<br />'.join(str(x.get(key_param)) for x in object)
    if return_data is None:
        return " - "
    return return_data


if __name__ == '__main__':

    with open("./chains/README.md", "w") as f:
        f.write(readme.render(
            networks_table=generate_networks_table()
        ))
