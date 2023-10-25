import pytest
import allure
from substrateinterface import SubstrateInterface
from scripts.utils.chain_model import Chain
from scripts.utils.metadata_interaction import get_properties
from tests.data.setting_data import get_substrate_chains

@allure.title("Test Chains")
@pytest.mark.core
class TestChains:
    chains = get_substrate_chains()

    @staticmethod
    def find_chain_by_id(chain_id) -> Chain | None:
        for chain in TestChains.chains:
            if chain.chainId == chain_id[2:]:
                return chain
        raise Exception(f'There is no chain with that chainId {chain_id}')

    @staticmethod
    def assert_url_in_chain_nodes(connection_by_url: SubstrateInterface, chain: Chain):
        assert connection_by_url.url in [node['url'] for node in chain.nodes], 'Check that this node is for proper chain'


    @allure.title("Test Address Prefix")
    def test_address_prefix(self, connection_by_url: SubstrateInterface):
        properies = get_properties(connection_by_url)
        chain = self.find_chain_by_id(properies.chainId)

        self.assert_url_in_chain_nodes(connection_by_url, chain)
        assert properies.ss58Format == chain.addressPrefix

    @allure.title("Test Chain ID")
    def test_chainId(self, connection_by_url: SubstrateInterface):
        properies = get_properties(connection_by_url)
        chain = self.find_chain_by_id(connection_by_url.get_block_hash(0))

        self.assert_url_in_chain_nodes(connection_by_url, chain)
        assert properies.chainId == '0x'+chain.chainId

    @allure.title("Test Precision")
    def test_precision(self, connection_by_url: SubstrateInterface):
        properies = get_properties(connection_by_url)
        chain = self.find_chain_by_id(connection_by_url.get_block_hash(0))

        self.assert_url_in_chain_nodes(connection_by_url, chain)
        assert properies.precision == chain.assets[0].get('precision')
