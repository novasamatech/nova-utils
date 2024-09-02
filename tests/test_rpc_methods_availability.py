import delayed_assert
from substrateinterface import SubstrateInterface

# "system_syncState" can be used for test, not available on Astar, Acala

rpc_methods = [
    "state_call", "state_getStorage", "state_getStorageSize", "state_getKeys",
    "state_getKeysPaged", "state_getMetadata", "state_subscribeRuntimeVersion", "system_syncState",
    "system_chain", "system_accountNextIndex", "state_subscribeStorage",
    "chain_getBlock", "chain_getBlockHash", "chain_getHeader", "chain_getFinalizedHead",
    "chain_getRuntimeVersion", "chain_subscribeRuntimeVersion",
    "childstate_getStorage", "system_properties", "payment_queryInfo",
    "author_submitExtrinsic", "author_submitAndWatchExtrinsic", "author_pendingExtrinsics"
]


# collected all results for repos under
# https://github.com/search?q=repo%3Anovasamatech%2Fsubstrate-sdk-android%20RuntimeRequest(&type=code
# https://github.com/search?q=repo%3Anovasamatech%2Fnova-wallet-android%20RuntimeRequest(&type=code
# excluded automationTime_getTimeAutomationFees and automationTime_calculateOptimalAutostaking as used only for Turing
# removed state_subscribeStorage stakingRewards_inflationInfo as absent practically in all nodes

def test_rpc_method_is_available(connection_by_url: SubstrateInterface):
    for method in rpc_methods:
        delayed_assert.expect(connection_by_url.supports_rpc_method(method),
                              "RPC method: " + method + " is not supported by node:" + connection_by_url.url)
    delayed_assert.assert_expectations()
