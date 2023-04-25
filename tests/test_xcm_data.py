import pytest
import json
import deepdiff

from tests.data.setting_data import get_substrate_chains
from scripts.utils.chain_model import Chain

xcm_data_file_path = './tests/data/xcm_data.json'

def was_network_data_changed(data_from_network, saved_data):
    diff = deepdiff.DeepDiff(data_from_network, saved_data)
    return diff.tree

task_ids = [
    f'Check XCM data for {task.name}'
    for task in get_substrate_chains()
]

@pytest.mark.parametrize('chain', get_substrate_chains(), ids=task_ids)
class TestCompareXCMData:

    def test_xcm_parameters(self, chain: Chain):
        connection = chain.create_connection()
        chain.init_properties()
        data = connection.get_constant('System', 'BlockWeights').serialize()

        with open(xcm_data_file_path) as fp:
            json_data = json.load(fp)
            changed_data = was_network_data_changed(data, json_data[chain.chainId]['BlockWeights'])
            assert not bool(changed_data)
