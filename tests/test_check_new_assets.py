import pytest
import delayed_assert
from scripts.utils.chain_model import Chain
from tests.data.setting_data import get_substrate_chains

task_ids = [
    f'Test for {task.name}'
    for task in get_substrate_chains()
]


@pytest.mark.parametrize("chain", get_substrate_chains(), ids=task_ids)
class TestAssets:
    # workaround to differences between asset names at runtime and in our configuration
    asset_mapping = {
        'AUSD': 'KUSD',
        'XX': 'xx'
    }
    
    def test_has_new_assets(self, chain: Chain):
        
        chain_assets = {asset['symbol'].upper(): '' for asset in chain.assets}
        chain_assets.update(self.asset_mapping)
        chain.create_connection()
        chain.init_properties()
        if isinstance(chain.substrate.token_symbol, list):
            for symbol in chain.substrate.token_symbol:
                delayed_assert.expect(symbol in chain_assets.keys() or symbol in chain_assets.values(), "new token to add: " + symbol)
        else:
            assert chain.properties.symbol in chain_assets.keys() or chain.properties.symbol in chain_assets.values(), "native asset has changed"
        delayed_assert.assert_expectations()
