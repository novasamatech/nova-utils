from substrateinterface import SubstrateInterface


def test_rpc_node_is_synced(connection_by_url: SubstrateInterface):
    sync_state = connection_by_url.rpc_request(
        method='system_syncState',
        params=[],
    ).get("result")

    if sync_state:
        current_block = sync_state['currentBlock']
        highest_block = sync_state['highestBlock']

        assert highest_block - current_block <= 100
    else:
        assert False, "Failed to retrieve SyncState"
