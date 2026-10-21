from scripts.xcm_transfers.xcm.multi_location import GlobalMultiLocation, RelativeMultiLocation
from scripts.xcm_transfers.xcm.versioned_xcm_builder import parachain_junction, global_consensus_ethereum_junction, \
    account_key20_junction


def test_reanchor_global_pov_should_remain_unchanged():

    initial = GlobalMultiLocation(junctions=[parachain_junction(1000)])
    pov = GlobalMultiLocation(junctions=[])
    expected = initial.as_relative()

    result = initial.reanchor(pov)

    assert result == expected


def test_no_common_junctions():
    initial = GlobalMultiLocation(junctions=[parachain_junction(1000)])
    pov = GlobalMultiLocation(junctions=[parachain_junction(2000)])
    expected = RelativeMultiLocation(parents=1, junctions=[parachain_junction(1000)])

    result = initial.reanchor(pov)

    assert result == expected

def test_one_common_junctions():
    initial = GlobalMultiLocation(junctions=[parachain_junction(1000), parachain_junction(2000)])
    pov = GlobalMultiLocation(junctions=[parachain_junction(1000), parachain_junction(3000)])
    expected = RelativeMultiLocation(parents=1, junctions=[parachain_junction(2000)])

    result = initial.reanchor(pov)

    assert result == expected

def test_all_common_junctions():
    initial = GlobalMultiLocation(junctions=[parachain_junction(1000), parachain_junction(2000)])
    pov = GlobalMultiLocation(junctions=[parachain_junction(1000), parachain_junction(2000)])
    expected = RelativeMultiLocation(parents=0, junctions=[])

    result = initial.reanchor(pov)

    assert result == expected

def test_global_to_global():
    initial = GlobalMultiLocation(junctions=[])
    pov = GlobalMultiLocation(junctions=[])
    expected = RelativeMultiLocation(parents=0, junctions=[])

    result = initial.reanchor(pov)

    assert result == expected

# This is "DOT on Relay from PAH pov" test
def test_pov_is_successor():
    initial = GlobalMultiLocation(junctions=[])
    pov = GlobalMultiLocation(junctions=[parachain_junction(1000)])
    expected = RelativeMultiLocation(parents=1, junctions=[])

    result = initial.reanchor(pov)

    assert result == expected


ETH = global_consensus_ethereum_junction(1)
WETH_CONTRACT = account_key20_junction("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")


# Snowbridge ETH from a parachain: one hop to the relay, one more to the universal level
def test_foreign_consensus_from_parachain():
    initial = GlobalMultiLocation(junctions=[ETH])
    pov = GlobalMultiLocation(junctions=[parachain_junction(1000)])
    expected = RelativeMultiLocation(parents=2, junctions=[ETH])

    assert initial.reanchor(pov) == expected


def test_foreign_consensus_from_relay():
    initial = GlobalMultiLocation(junctions=[ETH])
    pov = GlobalMultiLocation(junctions=[])
    expected = RelativeMultiLocation(parents=1, junctions=[ETH])

    assert initial.reanchor(pov) == expected


def test_foreign_consensus_erc20_from_parachain():
    initial = GlobalMultiLocation(junctions=[ETH, WETH_CONTRACT])
    pov = GlobalMultiLocation(junctions=[parachain_junction(2034)])
    expected = RelativeMultiLocation(parents=2, junctions=[ETH, WETH_CONTRACT])

    assert initial.reanchor(pov) == expected
