import json
import re
import os
import sys
from pathlib import Path
import requests
from scripts.utils.metadata_interaction import get_metadata_param, get_properties
from scripts.utils.substrate_interface import create_connection_by_url
from substrateinterface import SubstrateInterface
from enum import Enum
from utils.work_with_data import get_data_from_file

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.data.setting_data import get_substrate_chains

polkadot = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/productionRelayPolkadot.ts'
kusama = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/productionRelayKusama.ts'
westend = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayWestend.ts'
rococo = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayRococo.ts'
paseo = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testingRelayPaseo.ts'
singlechains = 'https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/production.ts'
testnets = "https://raw.githubusercontent.com/polkadot-js/apps/master/packages/apps-config/src/endpoints/testing.ts"

CHAINS_FILE_PATH_DEV = Path(os.getenv("DEV_CHAINS_JSON_PATH", 'chains/v20/chains_dev.json'))
CHAINS_FILE_PATH_PROD = Path(os.getenv("PROD_CHAINS_JSON_PATH", 'chains/v20/preConfigured/details'))


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


def get_ts_file(url):
    ts_file_path = "downloaded_file.ts"

    response = requests.get(url, stream=True)
    # Check if the request was successful
    if response.status_code == 200:
        # Open the file in write-binary mode
        with open(ts_file_path, "wb") as file:
            # Write the content of the response to the file in chunks
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    file.write(chunk)
        print(f"Downloaded file saved as {ts_file_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")


def ts_constant_to_json():
    json_file_path = "output.json"

    with open(json_file_path, 'r') as file:
        content = file.read()

    # Extract the array content
    array_match = re.search(r'=\s*\[(.*?)\]', content, re.DOTALL)
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

    return json_objects
    # Write the JSON array to the output file
    with open(json_file_path, 'w') as file:
        json.dump(json_objects, file, indent=2)
    print(f"Conversion completed. Output written to {json_file_path}")


def create_chain(chain_object):
    providers = chain_object.get("providers", {})
    # Get the first provider (if any)
    first_provider = None
    if providers:
        first_provider_value = next(iter(providers.values()), None)
        substrate = create_connection_by_url(first_provider_value.strip("'"))
        json_property = get_properties(substrate)

        providers = chain_object.get("providers")
        chain_data = {
            "chainId": json_property.chainId,
            "name": json_property.name,
            "assets": [{
                "assetId": 0,
                "symbol": json_property.symbol,
                "precision": json_property.precision,
                "icon": "https://raw.githubusercontent.com/novasamatech/nova-utils/master/icons/chains/white/Polkadot.svg"
            }],
            "nodes": [{"nodes": [{"url": url, "name": name} for name, url in providers.items()]}],
            "addressPrefix": json_property.ss58Format
        }
        return chain_data


def check_chain_id(chains, chain_id_to_check):
    for chain in chains:
        if chain.get("chainId") == chain_id_to_check:
            return True
    return False


def create_file(chain):
    file_name = CHAINS_FILE_PATH_DEV.__str__() + "preConfigured/details/" + chain.get("chainId")[2:] + ".json"
    save_json_file(file_name, chain)


def create_json_files(pjs_endpoints):
    existing_data_dev = load_json_file(CHAINS_FILE_PATH_DEV)
    # existing_data_prod = load_json_file(CHAINS_FILE_PATH_PROD)

    for item in pjs_endpoints:
        # skip disabled networks and networks with commented providers
        if '"isDisabled": "true"' in item or item.get("providers") == {}:
            continue
        else:
            chain = create_chain(item)
            chainid = chain.get("chainId")[2:]
            is_present = check_chain_id(existing_data_dev, chainid)
            if is_present:
                continue
            else:
                create_file(chain)


def main():
    get_ts_file(testnets)
    pjs_json = ts_constant_to_json()
    create_json_files(pjs_json)


if __name__ == "__main__":
    main()
