import io
import json

import pytest
from PIL import Image

from scripts.bittensor import update_subnets
from scripts.bittensor.chain_source import Subnet
from scripts.bittensor.update_subnets import LogoCandidate, fetch_logo, load_logo_overrides, logo_candidates

FIXTURES = "tests/bittensor/fixtures"


def subnet(netuid, logo_url_=None, name="Name"):
    return Subnet(netuid=netuid, name=name, symbol="α", logo_url=logo_url_)


def fixture(filename):
    with open(f"{FIXTURES}/{filename}", "rb") as f:
        return f.read()


def png_bytes(color):
    out = io.BytesIO()
    Image.new("RGBA", (8, 8), color).save(out, "PNG")
    return out.getvalue()


def test_candidates_are_ordered_override_chain_coingecko():
    subnets = [subnet(1, "https://chain/1.png"), subnet(2, "https://chain/2.png"), subnet(3)]
    overrides = {2: "https://manual/2.png"}
    coingecko = {1: "https://cg/1.png", 3: "https://cg/3.png"}

    assert logo_candidates(subnets, overrides, coingecko) == {
        1: [LogoCandidate("chain", "https://chain/1.png"), LogoCandidate("coingecko", "https://cg/1.png")],
        2: [LogoCandidate("override", "https://manual/2.png"), LogoCandidate("chain", "https://chain/2.png")],
        3: [LogoCandidate("coingecko", "https://cg/3.png")],
    }


def test_subnets_without_any_source_have_no_candidates():
    assert logo_candidates([subnet(7)], {}, {}) == {}


def test_override_for_unknown_subnet_is_ignored():
    assert logo_candidates([subnet(1)], {9: "https://manual/9.png"}, {}) == {}


def test_coingecko_listing_is_used_whatever_the_coin_is_named():
    # SN5 was OpenKaito when CoinGecko listed it and is Hone now; the listing's logo is still taken,
    # like Talisman does, so a subnet is not left without an icon.
    assert logo_candidates([subnet(5, name="Hone")], {}, {5: "https://cg/5.png"}) == {
        5: [LogoCandidate("coingecko", "https://cg/5.png")],
    }


def test_coingecko_listing_is_used_for_an_unnamed_subnet():
    assert logo_candidates([subnet(5, name=None)], {}, {5: "https://cg/5.png"}) == {
        5: [LogoCandidate("coingecko", "https://cg/5.png")],
    }


def test_fetch_logo_accepts_a_real_logo_from_coingecko(monkeypatch):
    monkeypatch.setattr(update_subnets, "download", lambda url: fixture("real_logo.png"))

    assert isinstance(fetch_logo([LogoCandidate("coingecko", "https://cg/61.png")]), bytes)


def test_fetch_logo_accepts_the_tao_placeholder_from_coingecko(monkeypatch):
    monkeypatch.setattr(update_subnets, "download", lambda url: fixture("coingecko_tao_placeholder.png"))

    assert isinstance(fetch_logo([LogoCandidate("coingecko", "https://cg/73.png")]), bytes)


def test_fetch_logo_uses_first_working_candidate(monkeypatch):
    red, blue = png_bytes((255, 0, 0, 255)), png_bytes((0, 0, 255, 255))

    def fake_download(url):
        if url == "https://chain/1.png":
            raise update_subnets.LogoError("html page")
        return {"https://cg/1.png": blue}[url]

    monkeypatch.setattr(update_subnets, "download", fake_download)

    outcome = fetch_logo([LogoCandidate("chain", "https://chain/1.png"), LogoCandidate("coingecko", "https://cg/1.png")])

    assert isinstance(outcome, bytes)
    assert Image.open(io.BytesIO(outcome)).getpixel((128, 128)) == (0, 0, 255, 255)
    assert outcome != update_subnets.normalize(red)


def test_fetch_logo_reports_every_failed_source(monkeypatch):
    def fake_download(url):
        raise update_subnets.LogoError("nope")

    monkeypatch.setattr(update_subnets, "download", fake_download)

    outcome = fetch_logo([LogoCandidate("chain", "https://chain/1.png"), LogoCandidate("coingecko", "https://cg/1.png")])

    assert outcome == "chain https://chain/1.png: LogoError: nope; coingecko https://cg/1.png: LogoError: nope"


def test_overrides_loaded_from_json_keyed_by_netuid(tmp_path):
    path = tmp_path / "logo-overrides.json"
    path.write_text(json.dumps({"12": "https://manual/12.png", "50": "https://manual/50.png"}))

    assert load_logo_overrides(str(path)) == {12: "https://manual/12.png", 50: "https://manual/50.png"}


def test_missing_overrides_file_means_no_overrides(tmp_path):
    assert load_logo_overrides(str(tmp_path / "absent.json")) == {}


def test_override_must_be_https(tmp_path):
    path = tmp_path / "logo-overrides.json"
    path.write_text(json.dumps({"12": "http://manual/12.png"}))

    with pytest.raises(ValueError):
        load_logo_overrides(str(path))


def test_fetch_logo_stops_at_the_first_failure_when_a_previous_logo_exists(monkeypatch):
    # A transient failure of the on-chain logo must keep yesterday's file, not swap in a lower source.
    tried = []

    def fake_download(url):
        tried.append(url)
        raise update_subnets.LogoError("timeout")

    monkeypatch.setattr(update_subnets, "download", fake_download)
    candidates = [LogoCandidate("chain", "https://chain/66.png"), LogoCandidate("coingecko", "https://cg/66.png")]

    outcome = fetch_logo(candidates, keep_previous=True)

    assert outcome == "chain https://chain/66.png: LogoError: timeout"
    assert tried == ["https://chain/66.png"]
