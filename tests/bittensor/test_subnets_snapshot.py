import json
import os

from scripts.bittensor.update_subnets import LOGO_BASE_URL, LOGO_DIR, SUBNETS_JSON, existing_logo_files


def load_entries():
    with open(SUBNETS_JSON, encoding="utf-8") as f:
        return json.load(f)["subnets"]


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
