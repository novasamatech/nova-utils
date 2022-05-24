import deepdiff
from pprint import pprint
import json


def compare_network(prod, dev):
    for network in prod:
        for dev_chain in dev:
            if (network['chainId'] == dev_chain['chainId']):
                diff = deepdiff.DeepDiff(network, dev_chain)
                print(network['name'])
                pprint(diff, indent=2)


with open("chains/v3/chains_dev.json") as fin:
    dev_chains = json.load(fin)


with open("chains/v3/chains.json") as fin:
    prod_chains = json.load(fin)

compare_network(prod_chains, dev_chains)

