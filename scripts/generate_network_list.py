#!/usr/bin/env python3


import json
import os
from jinja2 import Template
from pytablewriter import MarkdownTableWriter


readme = Template("""
{{networks_table}}
""")

CHAINS_VERSION = os.getenv('CHAINS_VERSION', default = "v4")


def generate_networks_table():
    writer = MarkdownTableWriter(
        table_name="List of supported networks",
        headers=["Network", "Assets", "Explorers", "SubQuery explorer"],
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
    return returning_array


def parse_parameters(key_param, object):
    if object is None:
        return " - "

    if type(object) is dict:
        data = object.get(key_param, " - ")
        if type(data) is str:
            return data
        return subquery_url_formator(data.get("url"))

    return_data = '<br />'.join(str(x.get(key_param)) for x in object)
    if return_data is None:
        return " - "
    return return_data


def subquery_url_formator(url):
    explorer_base_url = "https://explorer.subquery.network/subquery/nova-wallet/"

    if ("gapi" in url):
        organisation = "nova-"
        injecting_part = url.split("-")[1].split(".")[0]
        final_explorer_url = "[{name}]({link})".format(
            name=organisation+injecting_part, link=explorer_base_url + organisation + injecting_part)
        return final_explorer_url
    else:
        injecting_part = url.split("/")[-1]
        final_explorer_url = "[{name}]({link})".format(
            name=injecting_part, link=explorer_base_url + injecting_part)
        return final_explorer_url


if __name__ == '__main__':

    with open("./chains/README.md", "w") as f:
        f.write(readme.render(
            networks_table=generate_networks_table()
        ))
