from pprint import pprint
import json
import os
import deepdiff

CHAINS_VERISON = os.getenv('CHAINS_VERSION', default = "v6")

def compare_network(prod, dev):
    for network in prod:
        for dev_chain in dev:
            if (network['chainId'] == dev_chain['chainId']):
                diff = deepdiff.DeepDiff(network, dev_chain)
                print(network['name'])
                pprint(diff, indent=2)


with open(f"chains/{CHAINS_VERISON}/chains_dev.json") as fin:
    dev_chains = json.load(fin)


with open(f"chains/{CHAINS_VERISON}/chains.json") as fin:
    prod_chains = json.load(fin)

compare_network(prod_chains, dev_chains)
