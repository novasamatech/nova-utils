#!/usr/bin/env python3

"""
Generates the README for
[bamos/python-scripts](https://github.com/bamos/python-scripts)
so that the README and scripts contain synchronized documentation.
Script descriptions are obtained by parsing the docstrings
and inserted directly into the README as markdown.
"""

import json
import os
from jinja2 import Template
from pytablewriter import MarkdownTableWriter


readme = Template("""
# Nova Utils

## About
This repo contains static information (logos, links, etc) to support client apps in Polkadot & Kusama ecosystem (e.g. [Nova Wallet]) to map it to the keys/ids from the network itself.

Note: For better UX in your app its recommended to
1. prepare UI states & logic when this information cannot be fetched due to github unavailability
2. cache the data to cover part of the issue of 1.

## Modules
#### Crowdloan
Crowdloans can be saturated with the following information:
* id (to map the static data)
* Parachain name
* Description
* Logo
* Token
* Website
* Reward rate (KSM multiplier)

#### Chains
Contains JSON file with networks info: its token (ticker, precision), types, available nodes, account prefix, set of options (is testnet, has crowdloans)

#### Icons
Group of icons to saturate Nova Wallet

Note: Icons should be used from trusted sources, however currently icons are not available on the participants' websites, so for convenience, there is /icons folder.

{{networks_table}}
""")

def generate_networks_table():
    writer = MarkdownTableWriter(
        table_name="Our list of networks",
        headers=["Network", "Assets", "Explorers", "History", "Staking"],
        value_matrix=generate_value_matrix(),
        margin=1
    )
    writer.write_table()
    return writer


def generate_value_matrix():
    returning_array = []
    with open(os.getcwd()+"/chains/v2/chains.json", 'r') as json_file:
        data = json.load(json_file)
    for network in data:
        network_data_array = []
        network_data_array.append(network["name"])
        network_data_array.append(parse_parameters("symbol", network.get("assets")))
        network_data_array.append(parse_parameters("name", network.get("explorers")))
        network_data_array.append(parse_parameters("history", network.get("externalApi")))
        network_data_array.append(parse_parameters("staking", network.get("externalApi")))
        returning_array.append(network_data_array)
    return returning_array

def parse_parameters(key_param, object):
    if object is None: return " - "

    if type(object) is dict:
        data = object.get(key_param, " - ")
        if type(data) is str: return data
        return "[{name}]({link})".format(name=data.get("type"), link=data.get("url"))

    return_data =','.join(str(x.get(key_param)) for x in object)
    if return_data is None: return " - "
    return return_data



if __name__ == '__main__':
    # cd into the script directory.

    with open("README.md", "w") as f:
        f.write(readme.render(
            networks_table=generate_networks_table()
        ))