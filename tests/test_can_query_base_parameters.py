import os
import pytest
from tests.test_network_parameters import get_network_list
from tests.utils.chain_model import Chain
from substrateinterface import SubstrateInterface
from tests.data.setting_data import *

skipped_networks = ['Edgeware']
network_file_path = os.getenv('JSON_PATH', "/chains/v5/chains.json")

task_ids = [
    f'Test for {task.name}'
    for task in chains
]

@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestCanGetMetadata():

    def test_create_connection_and_get_metadata(self, chain: Chain):
        connection = chain.create_connection()
        chain.init_properties()

        metadata = connection.get_block_metadata()
        assert isinstance(connection, SubstrateInterface)

@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestCanGetFee:
    def test_create_connection_and_get_fee(self, chain: Chain):

        connection = chain.create_connection()
        chain.init_properties()

        storage = connection.rpc_request('payment_queryInfo', ['0x41028400fdc41550fb5186d71cae699c31731b3e1baa10680c7bd6b3831a6d222cf4d16800080bfe8bc67f44b498239887dc5679523cfcb1d20fd9ec9d6bae0a385cca118d2cb7ef9f4674d52a810feb32932d7c6fe3e05ce9e06cd72cf499c8692206410ab5038800040000340a806419d5e278172e45cb0e50da1b031795366c99ddfe0a680bd53b142c630700e40b5402'])
        assert isinstance(connection, SubstrateInterface)

@pytest.mark.parametrize("chain", chains, ids=task_ids)
class TestCanGetIndex:
    def test_create_connection_and_get_next_index(self, chain: Chain):

        connection = chain.create_connection()
        chain.init_properties()

        storage = connection.rpc_request('account_nextIndex', ['5CJqRchpnKQ6zzB4zmkz3QSzFgFmLFJ741RxW1CunStvEwKd'])
        assert isinstance(connection, SubstrateInterface)