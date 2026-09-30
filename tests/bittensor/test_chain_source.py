import json

import pytest

from scripts.bittensor.chain_source import (
    BITTENSOR_CHAIN_ID, ChainSourceError, Subnet, bittensor_node_urls, subnets_from_storage,
)


def test_maps_storage_to_subnets_sorted_by_netuid():
    added = {2: True, 0: True, 1: True}
    identities = {1: {"subnet_name": " Apex ", "logo_url": " https://x/logo.png "}}
    symbols = {0: "Τ", 1: "α", 2: "β"}

    assert subnets_from_storage(added, identities, symbols) == [
        Subnet(netuid=0, name=None, symbol="Τ", logo_url=None),
        Subnet(netuid=1, name="Apex", symbol="α", logo_url="https://x/logo.png"),
        Subnet(netuid=2, name=None, symbol="β", logo_url=None),
    ]


def test_skips_networks_not_added():
    assert subnets_from_storage({1: False, 2: True}, {}, {2: "β"}) == [
        Subnet(netuid=2, name=None, symbol="β", logo_url=None),
    ]


def test_empty_strings_become_none():
    identities = {3: {"subnet_name": "  ", "logo_url": ""}}
    assert subnets_from_storage({3: True}, identities, {3: "γ"}) == [
        Subnet(netuid=3, name=None, symbol="γ", logo_url=None),
    ]


def test_hex_encoded_bytes_are_decoded():
    identities = {4: {"subnet_name": "0x" + "Chutes".encode().hex(), "logo_url": None}}
    assert subnets_from_storage({4: True}, identities, {4: "0x" + "ش".encode().hex()}) == [
        Subnet(netuid=4, name="Chutes", symbol="ش", logo_url=None),
    ]


def test_node_urls_read_from_chains_file(tmp_path):
    chains = [
        {"chainId": "other", "nodes": [{"url": "wss://other"}]},
        {"chainId": BITTENSOR_CHAIN_ID, "nodes": [{"url": "wss://a"}, {"url": "wss://b"}]},
    ]
    path = tmp_path / "chains.json"
    path.write_text(json.dumps(chains))

    assert bittensor_node_urls(str(path)) == ["wss://a", "wss://b"]


def test_node_urls_missing_chain_raises(tmp_path):
    path = tmp_path / "chains.json"
    path.write_text("[]")

    with pytest.raises(ChainSourceError):
        bittensor_node_urls(str(path))
