import json

with open("chains.json") as fin:
    prod_chains = json.load(fin)

with open("chains_dev.json") as fin:
    dev_chains = json.load(fin)


def get_ids(chains):
    return list(map(lambda x: x["chainId"], chains))


prod_ids = get_ids(prod_chains)
dev_ids = get_ids(dev_chains)

prod_indices_by_id = dict(zip(prod_ids, range(0, len(prod_chains))))

for dev_index, dev_id in enumerate(dev_ids):
    if dev_id in prod_ids:
        prod_chains[prod_indices_by_id[dev_id]] = dev_chains[dev_index]


with open("chains.json", "w") as fout:
    json.dump(prod_chains, fout, indent=4)