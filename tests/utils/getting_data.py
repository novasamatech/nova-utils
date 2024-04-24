import os
import json

def get_network_list(path):

    dn = os.path.abspath('./')
    try:
        with open(dn + path) as fin:
            chains_data = json.load(fin)
    except:
        raise

    return chains_data