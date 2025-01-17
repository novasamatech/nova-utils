from substrateinterface import SubstrateInterface


class TestCanGetMetadata:
    def test_create_connection_and_get_metadata(self, connection_by_url: SubstrateInterface):
        metadata = connection_by_url.get_block_metadata()
        assert isinstance(connection_by_url, SubstrateInterface)


class TestCanGetFee:
    def test_create_connection_and_get_fee(self, connection_by_url: SubstrateInterface):
        storage = connection_by_url.rpc_request('payment_queryInfo', [
            '0x41028400fdc41550fb5186d71cae699c31731b3e1baa10680c7bd6b3831a6d222cf4d16800080bfe8bc67f44b498239887dc5679523cfcb1d20fd9ec9d6bae0a385cca118d2cb7ef9f4674d52a810feb32932d7c6fe3e05ce9e06cd72cf499c8692206410ab5038800040000340a806419d5e278172e45cb0e50da1b031795366c99ddfe0a680bd53b142c630700e40b5402'])
        assert isinstance(connection_by_url, SubstrateInterface)


class TestCanGetIndex:
    def test_create_connection_and_get_next_index(self, connection_by_url: SubstrateInterface):
        storage = connection_by_url.rpc_request('account_nextIndex',
                                                ['5CJqRchpnKQ6zzB4zmkz3QSzFgFmLFJ741RxW1CunStvEwKd'])
        assert isinstance(connection_by_url, SubstrateInterface)
