import json
import re
import os
import sys
from pathlib import Path
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.metadata_interaction import get_properties
from scripts.utils.substrate_interface import create_connection_by_url
from enum import Enum


class Endpoints(Enum):
    polkadot = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/productionRelayPolkadot.ts"
    kusama = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/productionRelayKusama.ts"
    singlechains = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/production.ts"
    testnet_westend = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayWestend.ts"
    testnet_rococo = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayRococo.ts"
    testnet_paseo = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayPaseo.ts"
    testnets = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testing.ts"


class BlacklistedChains(Enum):
    kulupu = 'f7a99d3cb92853d00d5275c971c132c074636256583fee53b3bbe60d7b8769ba'  # https://app.clickup.com/t/8695enz00
    nftmart = 'fcf9074303d8f319ad1bf0195b145871977e7c375883b834247cb01ff22f51f9'  # https://app.clickup.com/t/8695enz00


CHAINS_FILE_PATH_DEV = Path(os.getenv("DEV_CHAINS_JSON_PATH", 'chains/v20/chains_dev.json'))
CHAINS_FILE_PATH_PROD = Path(os.getenv("CHAINS_JSON_PATH", 'chains/v20/chains.json'))


def load_json_file(file_path):
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return []


def save_json_file(file_path, data):
    os.makedirs(Path(file_path).parent, exist_ok=True)
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

    return objects


def request_data_from_pjs(file):
    response = requests.get(file)
    data = response.json()
    return data


def get_ts_file(url, output_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"Downloaded file saved as {output_path}")
    except Exception as e:
        print(f"Failed to download file from {url}. Error: {e}")


def ts_constant_to_json(input_file_path):
    json_file_path = "output.json"

    with open(input_file_path, 'r') as file:
        content = file.read()

    # Extract the array content
    array_matches = re.findall(r'=\s*\[(.*?)\]', content, re.DOTALL)
    array_matches += re.findall(r'\[\s*(\{(?:.|\n)*?})\s*]', content, re.DOTALL)
    if not array_matches:
        raise ValueError("No array found in the input file")
    json_objects = []
    for i, array_content in enumerate(array_matches):
        # Split the array content into individual objects
        objects = find_objects(array_content)

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

    save_json_file(json_file_path, json_objects)
    print(f"Conversion completed. Output written to {json_file_path}")

    return json_objects


def create_chain_data(chain_object, endpoint_type):
    providers = chain_object.get("providers", {})
    if not providers:
        return None

    # Get the first provider (if any)
    # TODO: Iterate through all nodes available until connection is established
    first_provider_value = next(iter(providers.values()), None)
    wss_url = first_provider_value.strip("'")
    try:
        substrate = create_connection_by_url(wss_url)
        json_property = get_properties(substrate)

        chain_data = {
            "chainId": json_property.chainId[2:],
            "name": json_property.name,
            "assets": [{
                "assetId": 0,
                "symbol": json_property.symbol,
                "precision": json_property.precision,
                "icon": "https://raw.githubusercontent.com/novasamatech/nova-utils/master/icons/tokens/white/Default.svg"
            }],
            "nodes": [{"url": url, "name": name} for name, url in providers.items()],
            "addressPrefix": json_property.ss58Format
        }

        if "testnet" in endpoint_type:
            chain_data["name"] = chain_data.get("name") + " (TESTNET)"
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


def create_json_files(pjs_networks, chains_path, endpoint_name):
    existing_data_in_chains = load_json_file(chains_path)
    exclusion = "sora"

    for pjs_network in pjs_networks:
        # skip disabled networks and networks with commented providers
        pjs_chain_name = pjs_network.get("text")
        if '"isDisabled": "true"' in pjs_network or pjs_network.get("providers") == {}:
            continue
        chain = create_chain_data(pjs_network, endpoint_name)
        if chain:
            chain_id = chain.get("chainId")
            chain_name = chain.get("name")
            print(f"Connection established for {chain_name}")
            # skip chains already added to config
            is_chain_present = check_chain_id(existing_data_in_chains, chain_id)
            # skip chains with wss already added to config, in case they have changed chain_id
            is_node_present = check_node_is_present(existing_data_in_chains, chain.get("nodes"))
            if is_chain_present is False and is_node_present:
                print("⚠️Probably chainId is changed, check genesis for chain:" + chain_name)
            if (is_chain_present
                    or is_node_present
                    or exclusion.casefold() in chain_name.casefold()
                    or chain_id in [c.value for c in BlacklistedChains]):
                continue
            add_chains_details_file(chain, chains_path)
            add_chain_to_chains_file(chain, chains_path, endpoint_name)
        else:
            print(f"Skipped connection for chain {pjs_chain_name}")


def add_chains_details_file(chain, chains_path):
    if chains_path == CHAINS_FILE_PATH_DEV:
        target_path = chains_path.parent / 'preConfigured' / 'detailsDev'
    else:
        target_path = chains_path.parent / 'preConfigured' / 'details'
    file_name = chain.get("chainId") + '.json'
    file_path = target_path / file_name

    if file_path.exists():
        print(f"File found in config, skipping file: {file_name}")
    else:
        save_json_file(file_path, chain)
        print(f"Added details file for chain: {chain.get('name')}")


def add_chain_to_chains_file(chain, chains_path, endpoint_type):
    if chains_path == CHAINS_FILE_PATH_DEV:
        target_path = chains_path.parent / 'preConfigured' / 'chains_dev.json'
    else:
        target_path = chains_path.parent / 'preConfigured' / 'chains.json'
    chain_data = {
        "chainId": chain.get("chainId"),
        "name": chain.get("name")
    }

    data = load_json_file(target_path)
    chain_id_exists = any(item.get("chainId") == chain_data["chainId"] for item in data)

    if not chain_id_exists:
        data.append(chain_data)
        print(f"Added chain data to chains: {chain_data}")
    else:
        print(f"Chain ID {chain_data['chainId']} already exists in the file, skip adding")
    save_json_file(target_path, data)

def remove_files_except_shutting_down():
    work_dir = CHAINS_FILE_PATH_DEV.parent / 'preConfigured'

    for root, dirs, files in os.walk(work_dir):
        for item in files:
            if item.endswith('.json'):
                process_json_file(os.path.join(root, item))

def process_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, dict):
            process_dict_data(file_path, data)
        elif isinstance(data, list):
            process_list_data(file_path, data)
    except json.JSONDecodeError:
        print(f"Skipped non-JSON file: {file_path}")

def process_dict_data(file_path, data):
    if "(SHUTTING DOWN)" not in data.get('name', ''):
        os.remove(file_path)
        print(f"Removed file: {file_path}")

def process_list_data(file_path, data):
    shutting_down_items = [entry for entry in data if "(SHUTTING DOWN)" in entry.get('name', '')]
    if shutting_down_items:
        with open(file_path, 'w') as f:
            json.dump(shutting_down_items, f, indent=4)
        print(f"Updated file: {file_path}")
    else:
        os.remove(file_path)
        print(f"Removed file: {file_path}")


def main():
    ts_file_path = "downloaded_file.ts"
    remove_files_except_shutting_down()

    for endpoint in Endpoints:
        get_ts_file(endpoint.value, ts_file_path)
        polkadotjs_data = ts_constant_to_json(ts_file_path)
        create_json_files(polkadotjs_data, CHAINS_FILE_PATH_DEV, endpoint.name)
        create_json_files(polkadotjs_data, CHAINS_FILE_PATH_PROD, endpoint.name)


if __name__ == "__main__":
    main()
