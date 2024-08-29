import time

from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException


def test_rpc_node_is_synced(connection_by_url: SubstrateInterface):
    try:
        sync_state = connection_by_url.rpc_request(
            method='system_syncState',
            params=[],
        ).get("result")
        if sync_state:
            current_block = sync_state['currentBlock']
            highest_block = sync_state['highestBlock']
            assert highest_block - current_block < 300  # 30 min = 1 block ~ 6s * 300

        else:
            assert False, "Failed to retrieve SyncState"
    except SubstrateRequestException as err:
        # If we catch Method not found Exception -> then check internal network time
        system_timestamp = connection_by_url.query("Timestamp", "Now").value / 1000
        assert abs(time.time() - system_timestamp) < 1800  # 30 min = 30 * 60s
