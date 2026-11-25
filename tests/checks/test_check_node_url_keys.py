"""Offline tests of the provider key check; no node is contacted.

The module is loaded by path: importing the `scripts` package pulls in dependencies that the
pre-commit hook running these tests does not install.
"""

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "check_node_url_keys", REPOSITORY / "scripts" / "check_node_url_keys.py"
)
keys = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(keys)

HEX_KEY = "0123456789abcdef0123456789abcdef"
UUID_KEY = "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"

CLEAN_URLS = [
    "wss://rpc.polkadot.io",
    "wss://ethereum-rpc.publicnode.com",
    "https://1rpc.io/eth",
    "wss://polkadot.api.onfinality.io/public-ws",
    "wss://mainnet.zksync.io/zksync2-era/ws",
    "wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY}",
    "wss://api-polkadot-full.dwellir.com/{DWELLIR_API_KEY}",
    "wss://lb.drpc.org/ogws?network=ethereum",
    "wss://xode-polkadot-rpc-01.example.net/rpc",
    "wss://testrpcnodea01.example.net",
    "wss://node-6957502816543653888.lh.onfinality.io/ws",
    "https://data-seed-prebsc-1-s1.binance.org:8545",
]

KEYED_URLS = [
    # path
    f"wss://mainnet.infura.io/ws/v3/{HEX_KEY}",
    f"wss://bsc.getblock.io/{UUID_KEY}/mainnet/",
    "wss://xode-polkadot-rpc-01.zeeve.net/y0yx1a2b3c4d5e6/rpc",
    "wss://gateway.example/chain/abcdefghijklmnopqrstuvwxyzabcdef",
    f"wss://host.example/ws;{HEX_KEY}",
    f"wss://host.example/{HEX_KEY}.ws",
    f"wss://host.example/key:{HEX_KEY}/rpc",
    f"wss://host.example/{HEX_KEY}!",
    f"wss://host.example/project%3A{HEX_KEY}",
    "wss://host.example/a1b2c3d4e5f6g7h8%3D%3D/rpc",
    # query
    f"wss://host.example/ws?apikey={HEX_KEY}",
    f"wss://lb.drpc.org/ogws?network=ethereum&dkey={HEX_KEY}",
    "wss://host.example/ws?access_key=short",
    "wss://host.example/ws?auth=short",
    f"wss://host.example/ws?anything={HEX_KEY}",
    "wss://host.example/ws?x=abcd+0123456789abcdef0123",
    f"wss://host.example/ws?a=1;apikey={HEX_KEY}",
    f"wss://host.example/ws?{HEX_KEY}",
    f"wss://host.example/ws?{HEX_KEY}=1",
    # user info, host, fragment
    f"wss://user:{HEX_KEY}@host.example/ws",
    f"wss://{HEX_KEY}.rpc.example.com",
    f"wss://{UUID_KEY}.rpc.example.com",
    f"wss://host.example/ws#{HEX_KEY}",
    # placeholders the apps cannot substitute, or that would send their key to a foreign host
    "wss://mainnet.infura.io/ws/v3/{infura_api_key}",
    "wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY",
    "wss://mainnet.infura.io/ws/v3/{SOME_OTHER_KEY}",
    "wss://mainnet.infura.io/ws/v3/%7BINFURA_API_KEY%7D",
    "wss://mainnet.infura.io/ws?id={infura_api_key}",
    "wss://mainnet.infura.io/ws?id={SOME_OTHER_KEY}x",
    "wss://mainnet.infura.io/ws#{FOO_KEY}",
    "wss://{SOME_KEY}.example.com/ws",
    "wss://host.example/ws/{INFURA_API_KEY}",
    "wss://host.example/ws?apikey={INFURA_API_KEY}",
    "wss://infura.io.example/ws/{INFURA_API_KEY}",
    "wss://mainnet.infura.io/{DWELLIR_API_KEY}",
    # whitespace
    "wss://rpc.polkadot.io ",
]


@pytest.mark.parametrize("url", CLEAN_URLS)
def test_clean_url_passes(url):
    assert keys.problem_in(url) is None


@pytest.mark.parametrize("url", KEYED_URLS)
def test_keyed_url_is_reported(url):
    assert keys.problem_in(url) is not None


def write_config(tmp_path, config, name="chains.json"):
    path = tmp_path / name
    path.write_text(json.dumps(config), encoding="utf-8")

    return path


def chain(url, name="Chain"):
    return {"chainId": "0x01", "name": name, "nodes": [{"url": url, "name": "node"}]}


def test_nodes_are_found_in_a_chain_list_and_in_a_single_chain_details_file():
    in_list = list(keys.node_urls([chain("wss://a.example", "A"), chain("wss://b.example", "B")]))
    in_details = list(keys.node_urls(chain("wss://c.example", "C")))

    assert in_list == [("A", "wss://a.example"), ("B", "wss://b.example")]
    assert in_details == [("C", "wss://c.example")]


def test_new_keyed_url_is_an_error_and_does_not_print_the_key(tmp_path):
    path = write_config(tmp_path, [chain(KEYED_URLS[0], "Ethereum")])

    errors, known = keys.check(path, baseline=frozenset())

    assert len(errors) == 1 and "Ethereum" in errors[0]
    assert HEX_KEY not in errors[0]
    assert known == {}


def test_percent_encoded_key_is_not_printed(tmp_path):
    path = write_config(tmp_path, [chain("wss://host.example/ws?apikey=abcd%2B0123456789abcdef0123")])

    errors, _ = keys.check(path, baseline=frozenset())

    assert len(errors) == 1
    assert "0123456789abcdef0123" not in errors[0]


def test_baseline_exempts_the_exact_url_only(tmp_path):
    known_url = KEYED_URLS[1]
    other_key_on_the_same_host = known_url.replace("0a1b", "ffff")
    path = write_config(tmp_path, [chain(known_url, "Known"), chain(other_key_on_the_same_host, "New")])

    errors, known = keys.check(path, baseline=frozenset({keys.fingerprint(known_url)}))

    assert len(errors) == 1 and "New" in errors[0]
    assert list(known) == [keys.fingerprint(known_url)]


def test_false_positive_list_exempts_the_exact_url_only(tmp_path):
    harmless = "wss://rpc.example.com/mainnet-archive-v2"
    path = write_config(tmp_path, [chain(harmless, "Listed"), chain(harmless + "x", "Other")])

    errors, known = keys.check(path, baseline=frozenset(), false_positives=frozenset({harmless}))

    assert len(errors) == 1 and "Other" in errors[0]
    assert known == {}


def repository_node_urls():
    for path in sorted((REPOSITORY / "chains").rglob("*.json")):
        for _, url in keys.node_urls(json.loads(path.read_text(encoding="utf-8"))):
            yield url


def test_every_baseline_entry_is_still_in_the_configs():
    """The baseline only shrinks: a line whose URL has left the configs must be deleted."""
    present = {keys.fingerprint(url) for url in repository_node_urls()}

    assert keys.load_baseline() - present == set()


def test_false_positive_list_holds_no_keyed_url_of_the_baseline():
    listed = {keys.fingerprint(url) for url in keys.load_false_positives()}

    assert listed & keys.load_baseline() == set()


def test_exit_code_and_output(tmp_path, capsys):
    clean = write_config(tmp_path, [chain(CLEAN_URLS[0])], "clean.json")
    keyed = write_config(tmp_path, [chain(KEYED_URLS[0])], "keyed.json")

    assert keys.main([str(clean)]) == 0
    assert keys.main([str(clean), str(keyed)]) == 1
    assert "error:" in capsys.readouterr().err
