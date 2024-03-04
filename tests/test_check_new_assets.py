import delayed_assert
from scripts.utils.chain_model import Chain


class TestAssets:
    # workaround to differences between asset names at runtime and in our configuration
    asset_mapping = {
        'AUSD': 'KUSD',
        'RMRK (old)': 'RMRK'
    }
    # assets that has no working cases on network
    exclusions = {
        'Bifrost Kusama': {'DOT': ''},
        'Kintsugi': {'INTR': '', 'IBTC': '', 'DOT': ''},
        'Equilibrium': {'TOKEN': ''}
    }

    def test_has_new_assets(self, chain_model: Chain):

        chain_assets = {asset['symbol'].upper(
        ): '' for asset in chain_model.assets}
        chain_assets.update(self.asset_mapping)

        if chain_model.name in self.exclusions:
            chain_assets.update(
                {ex_asset: '' for ex_asset in self.exclusions[chain_model.name]})
        symbols = chain_model.substrate.token_symbol if isinstance(chain_model.substrate.token_symbol, list) else [
            chain_model.properties.symbol]

        for symbol in symbols:
            delayed_assert.expect(symbol.upper() in chain_assets.keys() or symbol.upper() in chain_assets.values(),
                                  "new token to add: " + symbol)

        delayed_assert.assert_expectations()
