"""Offline tests of the provider key check; no node is contacted."""

import json

import pytest

from scripts.check_node_url_keys import check, fingerprint, load_baseline, main, node_urls, problem_in

HEX_KEY = "0123456789abcdef0123456789abcdef"
UUID_KEY = "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"

CLEAN_URLS = [
    "wss://rpc.polkadot.io",
    "wss://ethereum-rpc.publicnode.com",
    "https://1rpc.io/eth",
    "wss://polkadot.api.onfinality.io/public-ws",
    "wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY}",
    "wss://api-polkadot.n.dwellir.com/{DWELLIR_API_KEY}",
    "wss://host.example/ws?apikey={INFURA_API_KEY}",
    "wss://lb.drpc.org/ogws?network=ethereum",
    "wss://xode-polkadot-rpc-01.example.net/rpc",
    "wss://testrpcnodea01.example.net",
    "wss://node-6957502816543653888.lh.onfinality.io/ws",
    "https://data-seed-prebsc-1-s1.binance.org:8545",
]

KEYED_URLS = [
    f"wss://mainnet.infura.io/ws/v3/{HEX_KEY}",
    f"wss://bsc.getblock.io/{UUID_KEY}/mainnet/",
    "wss://xode-polkadot-rpc-01.zeeve.net/y0yx1a2b3c4d5e6/rpc",
    "wss://gateway.example/chain/abcdefghijklmnopqrstuvwxyzabcdef",
    f"wss://host.example/ws?apikey={HEX_KEY}",
    f"wss://lb.drpc.org/ogws?network=ethereum&dkey={HEX_KEY}",
    "wss://host.example/ws?access_key=short",
    "wss://host.example/ws?auth=short",
    f"wss://host.example/ws?anything={HEX_KEY}",
    f"wss://user:{HEX_KEY}@host.example/ws",
    f"wss://{HEX_KEY}.rpc.example.com",
    f"wss://host.example/ws#{HEX_KEY}",
    f"wss://host.example/ws;{HEX_KEY}",
    f"wss://host.example/{HEX_KEY}.ws",
    "wss://host.example/a1b2c3d4e5f6g7h8%3D%3D/rpc",
    "wss://mainnet.infura.io/ws/v3/{infura_api_key}",
    "wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY",
    "wss://mainnet.infura.io/ws/v3/{SOME_OTHER_KEY}",
    "wss://host.example/ws?apikey={SOME_OTHER_KEY}",
    "wss://rpc.polkadot.io ",
]


@pytest.mark.parametrize("url", CLEAN_URLS)
def test_clean_url_passes(url):
    assert problem_in(url) is None


@pytest.mark.parametrize("url", KEYED_URLS)
def test_keyed_url_is_reported(url):
    assert problem_in(url) is not None


def write_config(tmp_path, config, name="chains.json"):
    path = tmp_path / name
    path.write_text(json.dumps(config), encoding="utf-8")

    return path


def chain(url, name="Chain"):
    return {"chainId": "0x01", "name": name, "nodes": [{"url": url, "name": "node"}]}


def test_nodes_are_found_in_a_chain_list_and_in_a_single_chain_details_file():
    in_list = list(node_urls([chain("wss://a.example", "A"), chain("wss://b.example", "B")]))
    in_details = list(node_urls(chain("wss://c.example", "C")))

    assert in_list == [("A", "wss://a.example"), ("B", "wss://b.example")]
    assert in_details == [("C", "wss://c.example")]


def test_new_keyed_url_is_an_error_and_does_not_print_the_key(tmp_path):
    path = write_config(tmp_path, [chain(KEYED_URLS[0], "Ethereum")])

    errors, known = check(path, baseline=frozenset())

    assert len(errors) == 1 and "Ethereum" in errors[0]
    assert HEX_KEY not in errors[0]
    assert known == {}


def test_percent_encoded_key_is_not_printed(tmp_path):
    path = write_config(tmp_path, [chain("wss://host.example/ws?apikey=abcd%2B0123456789abcdef0123")])

    errors, _ = check(path, baseline=frozenset())

    assert len(errors) == 1
    assert "0123456789abcdef0123" not in errors[0]


def test_baseline_exempts_the_exact_url_only(tmp_path):
    known_url = KEYED_URLS[1]
    other_key_on_the_same_host = known_url.replace("0a1b", "ffff")
    path = write_config(tmp_path, [chain(known_url, "Known"), chain(other_key_on_the_same_host, "New")])

    errors, known = check(path, baseline=frozenset({fingerprint(known_url)}))

    assert len(errors) == 1 and "New" in errors[0]
    assert list(known) == [fingerprint(known_url)]


def test_repository_baseline_holds_fingerprints_only():
    baseline = load_baseline()

    assert baseline
    assert all(len(entry) == 64 and set(entry) <= set("0123456789abcdef") for entry in baseline)


def test_exit_code_and_output(tmp_path, capsys):
    clean = write_config(tmp_path, [chain(CLEAN_URLS[0])], "clean.json")
    keyed = write_config(tmp_path, [chain(KEYED_URLS[0])], "keyed.json")

    assert main([str(clean)]) == 0
    assert main([str(clean), str(keyed)]) == 1
    assert "error:" in capsys.readouterr().err
