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


def test_github_blob_logo_url_is_rewritten_to_raw():
    identities = {5: {"subnet_name": "ItsAI", "logo_url": "https://github.com/It-s-AI/llm-detection/blob/main/full_logo.png"}}
    assert subnets_from_storage({5: True}, identities, {5: "ε"})[0].logo_url == (
        "https://raw.githubusercontent.com/It-s-AI/llm-detection/main/full_logo.png"
    )


def test_non_blob_github_logo_url_is_kept():
    url = "https://raw.githubusercontent.com/a/b/main/logo.png"
    identities = {5: {"subnet_name": "x", "logo_url": url}}
    assert subnets_from_storage({5: True}, identities, {5: "ε"})[0].logo_url == url


def test_dropbox_share_page_logo_url_becomes_a_direct_download():
    shared = "https://www.dropbox.com/scl/fi/abc/logo.svg?rlkey=k&st=s&dl=0"
    identities = {6: {"subnet_name": "Claims", "logo_url": shared}}
    assert subnets_from_storage({6: True}, identities, {6: "ζ"})[0].logo_url == (
        "https://www.dropbox.com/scl/fi/abc/logo.svg?rlkey=k&st=s&dl=1"
    )


def test_dropbox_dl_parameter_is_only_rewritten_on_dropbox():
    url = "https://example.com/logo.png?dl=0"
    identities = {6: {"subnet_name": "x", "logo_url": url}}
    assert subnets_from_storage({6: True}, identities, {6: "ζ"})[0].logo_url == url
