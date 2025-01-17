from scripts.utils.chain_model import Chain


class TestNetworkPrefix:
    def test_address_prefix(self, chain_model: Chain):
        assert chain_model.properties.ss58Format == chain_model.addressPrefix


class TestChainId:
    def test_chainId(self, chain_model: Chain):
        assert chain_model.properties.chainId == '0x' + chain_model.chainId


class TestPrecision:
    def test_precision(self, chain_model: Chain):
        assert chain_model.properties.precision == chain_model.assets[0].get('precision')
