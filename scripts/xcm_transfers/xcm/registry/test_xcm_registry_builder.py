import pytest

from scripts.xcm_transfers.xcm.registry.xcm_registry_builder import _map_junction_from_config, \
    _junctions_from_config


def test_global_consensus_ethereum():
    result = _map_junction_from_config("globalConsensus", {"ethereum": {"chainId": 1}})

    assert result == {"GlobalConsensus": {"Ethereum": {"chain_id": 1}}}


def test_account_key20():
    result = _map_junction_from_config("accountKey20", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")

    assert result == {"AccountKey20": {"network": None, "key": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"}}


def test_unsupported_global_consensus_raises():
    with pytest.raises(Exception):
        _map_junction_from_config("globalConsensus", {"polkadot": {}})


def test_unknown_junction_key_raises():
    with pytest.raises(Exception):
        _map_junction_from_config("parents", 2)


def test_global_consensus_is_ordered_first():
    config = {
        "accountKey20": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "globalConsensus": {"ethereum": {"chainId": 1}},
    }

    junctions = _junctions_from_config(config)

    assert list(junctions[0].keys()) == ["GlobalConsensus"]
    assert list(junctions[1].keys()) == ["AccountKey20"]
