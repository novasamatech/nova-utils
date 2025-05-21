import json
import os

from scripts.utils.chain_model import Chain

CHAINS_VERSION = Chain.latest_config_version()

with open(f"chains/{CHAINS_VERSION}/chains_dev.json") as fin:
    dev_chains = json.load(fin)
    # Skip paused networks
    dev_chains = [chain for chain in dev_chains if 'PAUSED' not in chain['name']]

with open("tests/chains_for_testBalance.json") as fin:
    test_chains = json.load(fin)


def get_ids(chains):
    return list(map(lambda x: x["chainId"], chains))


exludeChains = ['Kintsugi', 'Interlay', 'Mangata X', 'Fusotao', 'Equilibrium', 'Crust']
skip_options = ['ethereumBased', 'noSubstrateRuntime', 'testnet']

dev_ids = get_ids(dev_chains)
test_ids = get_ids(test_chains)

dev_indices_by_id = dict(zip(dev_ids, range(0, len(dev_chains))))

def del_element(test_ids):
    """This is a recursive function
    to safety remove item from the list"""
    for test_index, test_id in enumerate(test_ids):
        if test_id not in dev_ids:
            test_chains.pop(test_index)
            test_ids.pop(test_index)
            return del_element(test_ids)


del_element(test_ids)


for dev_index, dev_id in enumerate(dev_ids):  # Add new network

    if dev_id not in test_ids:
        chain_dict = {
            'chainId': dev_chains[dev_index]['chainId'],
            'name': dev_chains[dev_index]['name'],
            'account': ' - '}

        options = dev_chains[dev_index].get('options')

        if (dev_chains[dev_index]['name'] in exludeChains):  # Skip some special chains
            continue

        if options is not None:
            need_skip = [option for option in skip_options if option in options]
            if need_skip: continue

        test_chains.append(chain_dict)


with open("tests/chains_for_testBalance.json", "w") as fout:
    json.dump(test_chains, fout, indent=4)
    fout.write("\n")
