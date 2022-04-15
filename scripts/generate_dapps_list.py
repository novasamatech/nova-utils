#!/usr/bin/env python3


import json
import os
from jinja2 import Template
from pytablewriter import MarkdownTableWriter

readme = Template("""
{{dapps_table}}
""")


def generate_dapps_table():
    writer = MarkdownTableWriter(
        table_name="List of supported dapps",
        headers=["DApp", "Url", "Tags"],
        value_matrix=generate_value_matrix(),
        margin=1
    )
    writer.write_table()
    return writer


def generate_value_matrix():
    returning_array = []
    with open(os.getcwd() + f"/dapps/dapps.json", 'r') as json_file:
        data = json.load(json_file)
    for dapp in data['dapps']:
        network_data_array = []
        network_data_array.append(dapp["name"])
        network_data_array.append(dapp["url"])
        network_data_array.append(",".join(dapp["categories"]))
        returning_array.append(network_data_array)
    return returning_array


if __name__ == '__main__':
    with open("./dapps/README.md", "w") as f:
        f.write(readme.render(
            dapps_table=generate_dapps_table()
        ))
