import pytest

from scripts.utils.chain_model import Chain
from tests.data.setting_data import chains

task_ids = [
    f'Test for {task.name}'
    for task in chains
]

@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestNetworkPrefix:
    def test_address_prefix(self, chain: Chain):
        chain.create_connection()
        chain.init_properties()
        assert chain.properties.ss58Format == chain.addressPrefix

@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestChainId:
    def test_chainId(self, chain: Chain):
        chain.create_connection()
        chain.init_properties()
        assert chain.properties.chainId == '0x'+chain.chainId

@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestPrecision:
    def test_precision(self, chain: Chain):
        chain.create_connection()
        chain.init_properties()
        assert chain.properties.precision == chain.assets[0].get('precision')
