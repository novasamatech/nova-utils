from distutils.log import error
import json
from substrateinterface import SubstrateInterface

def create_connection(url):
    try:
        substrate = SubstrateInterface(
            url=url
        )
        return substrate
    except:
        print(f"Found {error=}, {type(error)=}")
        print (url)
        return False


with open("chains/v3/chains_dev.json") as fin:
    dev_chains = json.load(fin)


for chain in dev_chains:
    for node in chain['nodes']:
        sub_object = create_connection(node['url'])
        if (sub_object):
            print('My url is: \n' + sub_object.url)
            print('Network is: \n' + sub_object.chain)
            print('\n')
            sub_object.close()




