from substrateinterface import SubstrateInterface


def test_can_create_connection(connection_by_url: SubstrateInterface):
    assert isinstance(connection_by_url, SubstrateInterface)
