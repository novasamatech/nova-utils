import delayed_assert
from substrateinterface import SubstrateInterface

rpc_methods = [
    "state_call", "state_getStorage", "state_subscribeStorage",
    "state_getKeysPaged", "state_getMetadata", "state_subscribeRuntimeVersion",
    "system_chain", "system_accountNextIndex", "system_properties",
    "chain_getBlock", "chain_getBlockHash", "chain_getHeader", "chain_getFinalizedHead",
    "childstate_getStorage",
    "author_submitExtrinsic", "author_submitAndWatchExtrinsic", "author_pendingExtrinsics"
]


# collected all results for repos under
# https://github.com/search?q=repo%3Anovasamatech%2Fsubstrate-sdk-android%20RuntimeRequest(&type=code
# https://github.com/search?q=repo%3Anovasamatech%2Fnova-wallet-android%20RuntimeRequest(&type=code
# excluded automationTime_getTimeAutomationFees and automationTime_calculateOptimalAutostaking as used only for Turing
# excluded stakingRewards_inflationInfo as absent practically in all nodes
# excluded payment_queryInfo is needed only if no feeViaRuntimeCall
# excluded chain_getRuntimeVersion as replaced with state_subscribeRuntimeVersion
# excluded state_getStorageSize as required only in OpenGov
# excluded state_getKeys as used as fallback for not getting state_getKeysPaged in pending rewards
# system_syncState can be used for test, not available on Acala, Astar


def test_rpc_method_is_available(connection_by_url: SubstrateInterface):
    for method in rpc_methods:
        delayed_assert.expect(connection_by_url.supports_rpc_method(method),
                              "RPC method: " + method + " is not supported by node:" + connection_by_url.url)
    delayed_assert.assert_expectations()
