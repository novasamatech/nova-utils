import json
import re
import os
import sys
from pathlib import Path
import requests
from scripts.utils.metadata_interaction import get_properties
from scripts.utils.substrate_interface import create_connection_by_url
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Endpoints(Enum):
    polkadot = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/productionRelayPolkadot.ts'
    kusama = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/productionRelayKusama.ts'
    westend = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayWestend.ts'
    rococo = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayRococo.ts'
    paseo = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayPaseo.ts'
    singlechains = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/production.ts'
    testnets = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testing.ts"


CHAINS_FILE_PATH_DEV = Path(os.getenv("DEV_CHAINS_JSON_PATH", 'chains/v20/chains_dev.json'))
CHAINS_FILE_PATH_PROD = Path(os.getenv("PROD_CHAINS_JSON_PATH", 'chains/v20/chains.json'))


def load_json_file(file_path):
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return []


def save_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
        f.write('\n')


def find_objects(array_content):
    objects = []
    stack = []
    start = -1

    for i, char in enumerate(array_content):
        if char == '{':
            if not stack:
                start = i
            stack.append(char)
        elif char == '}':
            if stack and stack[-1] == '{':
                stack.pop()
                if not stack:
                    objects.append(array_content[start:i + 1])
            else:
                # Mismatched braces, handle error as needed
                pass

    return objects


def request_data_from_pjs(file):
    response = requests.get(file)
    data = response.json()
    return data


def get_ts_file(url, output_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"Downloaded file saved as {output_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")


def ts_constant_to_json(input_file_path):
    json_file_path = "output.json"

    with open(input_file_path, 'r') as file:
        content = file.read()

    # Extract the array content
    array_match = re.search(r'=\s*\[(.*?)]', content, re.DOTALL)
    if not array_match:
        raise ValueError("No array found in the input file")

    array_content = array_match.group(1)

    # Split the array content into individual objects
    objects = find_objects(array_content)
    json_objects = []

    for obj in objects:
        # Remove comments
        obj_lines = [line for line in obj.split('\n') if not line.strip().startswith('//')]
        cleaned_obj = '\n'.join(obj_lines)

        # Convert to valid JSON
        cleaned_obj = re.sub(r"'", '"', cleaned_obj)  # Replace single quotes with double quotes
        cleaned_obj = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', cleaned_obj)  # Add quotes to keys
        cleaned_obj = re.sub(r",\s*}", "}", cleaned_obj)  # Remove trailing commas
        cleaned_obj = re.sub(r":\s*([a-zA-Z]\w*)", r': "\1"', cleaned_obj)  # Quote unquoted string values
        cleaned_obj = re.sub(r"\n", '', cleaned_obj)

        # Parse the cleaned object
        try:
            json_obj = json.loads(cleaned_obj)
            json_objects.append(json_obj)
        except json.JSONDecodeError as e:
            print(f"Error parsing object: {e}")
            print(f"Problematic object: {cleaned_obj}")

    # Write the JSON array to the output file
    with open(json_file_path, 'w') as file:
        json.dump(json_objects, file, indent=2)
        print(f"Conversion completed. Output written to {json_file_path}")
        return json_objects


def create_chain_data(chain_object):
    providers = chain_object.get("providers", {})
    # Get the first provider (if any)
    # TODO: Iterate through all nodes available until connection is established
    first_provider = None
    if providers:
        first_provider_value = next(iter(providers.values()), None)
        wss_url = first_provider_value.strip("'")
        try:
            substrate = create_connection_by_url(wss_url)

            json_property = get_properties(substrate)
            providers = chain_object.get("providers")

            chain_data = {
                "chainId": json_property.chainId[2:],
                "name": chain_object.get("text"),
                "assets": [{
                    "assetId": 0,
                    "symbol": json_property.symbol,
                    "precision": json_property.precision,
                    "icon": "https://raw.githubusercontent.com/novasamatech/nova-utils/master/icons/chains/white/Polkadot.svg"
                }],
                "nodes": [{"url": url, "name": name} for name, url in providers.items()],
                "addressPrefix": json_property.ss58Format
            }
            return chain_data
        except Exception as err:
            # If there's a failure, print a warning and skip the connection
            print(f"⚠️ Can't connect by {wss_url}, check if it is available? \n {err}")
            # Do not raise the exception; instead, return None or handle it accordingly
            return None


def check_chain_id(chains, chain_id_to_check):
    for chain in chains:
        if chain.get("chainId") == chain_id_to_check:
            return True
    return False


def check_node_is_present(chains_data, nodes_to_check):
    # Iterate over each node to check
    for node in nodes_to_check:
        node_url = node['url']
        found = False
        # Iterate over each chain in the chain data
        for chain in chains_data:
            # Check if node URL exists in any node list of this chain
            if any(n['url'] == node_url for n in chain['nodes']):
                found = True
                print(f"⚠️Node URL '{node_url}' is found in chain '{chain['name']}'.")
                break
        if not found:
            return False
    return True


def add_chains_details_file(chain, chains_path):
    target_path = chains_path.parent / 'preConfigured' / 'detailsDev'
    file_name = chain.get("chainId") + '.json'
    file_path = target_path / file_name

    if file_path.exists():
        print(f"File found in config, kipping file: {file_name}")
    else:
        print(f"File not found, continuing processing.")
        save_json_file(file_path, chain)
        print(f"Created file for chain {chain.get('name')}")


def add_chain_to_chains_file(chain, chains_path):
    target_path = chains_path.parent / 'preConfigured' / 'chains_dev.json'
    chain_data = {
        "chainId": chain.get("chainId"),
        "name": chain.get("name")
    }

    with open(target_path, 'r') as file:
        data = json.load(file)
    chain_id_exists = any(item.get("chainId") == chain_data["chainId"] for item in data)

    if not chain_id_exists:
        data.append(chain_data)
        print(f"Added new chain data: {chain_data}")
    else:
        print(f"Chain ID {chain_data['chainId']} already exists in the file.")
    save_json_file(target_path, data)


def create_json_files(pjs_networks, chains_path):
    existing_data_in_chains = load_json_file(chains_path)

    for pjs_network in pjs_networks:
        # skip disabled networks and networks with commented providers
        pjs_chain_name = pjs_network.get("text")
        if '"isDisabled": "true"' in pjs_network or pjs_network.get("providers") == {}:
            continue
        else:
            chain = create_chain_data(pjs_network)
            if chain:
                chain_name = chain.get("name")
                print(f"Connection established for {chain_name}")
                chain_id = chain.get("chainId")
                # skip chains already added to config
                is_chain_present = check_chain_id(existing_data_in_chains, chain_id)
                # skip chains with wss already added to config, in case they have changed chain_id
                is_node_present = check_node_is_present(existing_data_in_chains, chain.get("nodes"))
                if is_chain_present or is_node_present:
                    continue
                else:
                    add_chains_details_file(chain, chains_path)
                    add_chain_to_chains_file(chain, chains_path)
            else:
                print(f"Skipped connection for chain {pjs_chain_name}")


def main():
    ts_file_path = "downloaded_file.ts"

    get_ts_file(Endpoints.testnets.value, ts_file_path)
    polkadotjs_json = ts_constant_to_json(ts_file_path)
    create_json_files(polkadotjs_json, CHAINS_FILE_PATH_DEV)


if __name__ == "__main__":
    main()
