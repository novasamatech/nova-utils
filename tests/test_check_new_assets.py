import pytest
import delayed_assert
from scripts.utils.chain_model import Chain
from tests.data.setting_data import chains

task_ids = [
    f'Test for {task.name}'
    for task in chains
]


@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestAssets:
    def test_has_new_assets(self, chain: Chain):
        added_assets = []
        for asset in chain.assets:
            added_assets.append(asset['symbol'].upper())
        chain.create_connection()
        chain.init_properties()
        if isinstance(chain.substrate.token_symbol, list):
            for symbol in chain.substrate.token_symbol:
                delayed_assert.expect(symbol in added_assets, "new token to add: " + symbol)
        else:
            assert chain.assets[0]['symbol'] == chain.properties.symbol, "native asset has changed"
        delayed_assert.assert_expectations()
