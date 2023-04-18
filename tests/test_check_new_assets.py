import pytest
from scripts.utils.chain_model import Chain
from tests.data.setting_data import chains

task_ids = [
    f'Test for {task.name}'
    for task in chains
]


@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestAssets:
    def test_has_new_assets(self, chain: Chain):
        chain.create_connection()
        chain.init_properties()
        assets = []
        for asset in chain.assets:
            assets.append(asset['symbol'].upper())
        if isinstance(chain.substrate.token_symbol, list):
            for symbol in chain.substrate.token_symbol:
                assert symbol in assets
        else:
            assert chain.properties.symbol == chain.assets[0]['symbol']
