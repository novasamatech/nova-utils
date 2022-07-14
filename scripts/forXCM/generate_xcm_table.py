#!/usr/bin/env python3

from jinja2 import Template
from pytablewriter import MarkdownTableWriter
from utils.xcm_сhain import XcmChain
from utils.useful_functions import parse_json_file

readme = Template("""
{{xcm_table}}
""")
xcm_json_path = './xcm/v2/transfers_dev.json'
chains_json_path = './chains/v4/chains_dev.json'


def generate_xcm_table():
    writer = MarkdownTableWriter(
        table_name="List of supported xcm Transfers",
        headers=[" - ", "Source Network", "Assets"],
        value_matrix=generate_value_matrix(),
        margin=1
    )
    writer.write_table()
    return writer


def generate_value_matrix():
    returning_array = []
    xcm_data = build_data_from_jsons()
    for xcm in xcm_data:
        current_xcm = []
        current_xcm.append(xcm.chainName)
        destinations = []
        for asset in xcm.assets:
            destinations.append(asset.get('asset') + ' -> ' +
                                ','.join(asset.get('destination')))
        current_xcm.append('<br/>'.join(destinations))
        returning_array.append(current_xcm)
    returning_array.sort()
    increment = iter(range(1, len(returning_array)+1))
    [network.insert(0, next(increment)) for network in returning_array]
    return returning_array


def build_data_from_jsons():
    xcm_json_data = parse_json_file(xcm_json_path)
    chains_json_data = parse_json_file(chains_json_path)
    processed_xcm_chains = []
    for xcm in xcm_json_data.get('chains'):
        processed_xcm_chains.append(XcmChain(xcm, chains_json_data))
    return processed_xcm_chains


if __name__ == '__main__':

    with open("./xcm/README.md", "w") as f:
        f.write(readme.render(
            xcm_table=generate_xcm_table()
        ))
