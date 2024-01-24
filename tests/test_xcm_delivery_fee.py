import pytest
from scripts.utils.chain_model import Chain
from tests.data.setting_data import get_parachains_with_xcm, get_relaychains_with_xcm


parachain_chain_names = [
    f'Test for {task.name}'
    for task in get_parachains_with_xcm()
]

relaychain_chain_names = [
    f'Test for {task.name}'
    for task in get_relaychains_with_xcm()
]

class TestXCMDeliveryFee:


    @pytest.mark.parametrize('chain_model', get_parachains_with_xcm(), ids=parachain_chain_names, indirect=True)
    def test_parachain_has_delivery_factor(self, chain_model: Chain):
        data = chain_model.substrate.get_metadata_storage_function(module_name='XcmpQueue', storage_name='DeliveryFeeFactor')
        assert data is None

    @pytest.mark.parametrize('chain_model', get_relaychains_with_xcm(), ids=relaychain_chain_names, indirect=True)
    def test_relaychain_has_delivery_factor(self, chain_model: Chain):
        data = chain_model.substrate.get_metadata_storage_function(module_name='Dmp', storage_name='DeliveryFeeFactor')
        assert data is None
