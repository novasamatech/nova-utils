import json
import os

from scripts.bittensor.update_subnets import CONFIG_JSON, LOGO_BASE_URL, LOGO_DIR, existing_logo_files


def load_config():
    with open(CONFIG_JSON, encoding="utf-8") as f:
        return json.load(f)


def load_entries():
    return load_config()["subnets"]


def test_swap_fee_is_a_percent():
    swap_fee = load_config()["swapFee"]
    assert type(swap_fee) in (int, float) and 0 <= swap_fee < 100, swap_fee


def test_entries_are_sorted_and_unique():
    netuids = [e["netuid"] for e in load_entries()]
    assert netuids == sorted(set(netuids))


def test_every_logo_points_to_existing_file():
    for e in load_entries():
        if e["logo"]:
            assert e["logo"].startswith(LOGO_BASE_URL + "/"), e
            assert os.path.isfile(os.path.join(LOGO_DIR, e["logo"].rsplit("/", 1)[-1])), e


def test_no_unreferenced_logo_files():
    referenced = {e["logo"].rsplit("/", 1)[-1] for e in load_entries() if e["logo"]}
    assert set(existing_logo_files(LOGO_DIR)) == referenced
