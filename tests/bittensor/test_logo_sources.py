import io
import json

import pytest
from PIL import Image

from scripts.bittensor import update_subnets
from scripts.bittensor.chain_source import Subnet
from scripts.bittensor.price_source import CoinGeckoLogo
from scripts.bittensor.update_subnets import (
    LogoCandidate, fetch_logo, is_tao_placeholder, load_logo_overrides, logo_candidates, names_match,
)

FIXTURES = "tests/bittensor/fixtures"


def subnet(netuid, logo_url_=None, name="Name"):
    return Subnet(netuid=netuid, name=name, symbol="α", logo_url=logo_url_)


def cg(url, name="Name"):
    return CoinGeckoLogo(name=name, url=url)


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
    coingecko = {1: cg("https://cg/1.png"), 3: cg("https://cg/3.png")}

    assert logo_candidates(subnets, overrides, coingecko) == {
        1: [LogoCandidate("chain", "https://chain/1.png"), LogoCandidate("coingecko", "https://cg/1.png")],
        2: [LogoCandidate("override", "https://manual/2.png"), LogoCandidate("chain", "https://chain/2.png")],
        3: [LogoCandidate("coingecko", "https://cg/3.png")],
    }


def test_subnets_without_any_source_have_no_candidates():
    assert logo_candidates([subnet(7)], {}, {}) == {}


def test_override_for_unknown_subnet_is_ignored():
    assert logo_candidates([subnet(1)], {9: "https://manual/9.png"}, {}) == {}


def test_coingecko_listing_of_a_differently_named_coin_may_only_give_the_placeholder():
    # SN5 was OpenKaito when CoinGecko listed it and is Hone now: the Kaito logo would be wrong,
    # the generic TAO placeholder cannot be.
    assert logo_candidates([subnet(5, name="Hone")], {}, {5: cg("https://cg/5.png", name="OpenKaito")}) == {
        5: [LogoCandidate("coingecko", "https://cg/5.png", placeholder_only=True)],
    }


def test_coingecko_listing_without_a_subnet_name_to_match_against_may_only_give_the_placeholder():
    assert logo_candidates([subnet(5, name=None)], {}, {5: cg("https://cg/5.png", name="LogicNet")}) == {
        5: [LogoCandidate("coingecko", "https://cg/5.png", placeholder_only=True)],
    }


@pytest.mark.parametrize("subnet_name, coin_name", [
    ("Compute Horde", "Compute Horde"),
    ("Bitsec.ai", "Bitsec AI"),
    ("RedTeam", "redteam"),
    ("StreetVision by NATIX", "StreetVision"),
    ("Dojo", "Dojo Subnet"),
])
def test_names_match_ignores_case_punctuation_and_suffixes(subnet_name, coin_name):
    assert names_match(subnet_name, coin_name)


@pytest.mark.parametrize("subnet_name, coin_name", [
    ("Hone", "OpenKaito"),
    ("Finsight", "Taoillium"),
    ("Parked", "Merit"),
    ("AI", "ReadyAI"),
    (None, "LogicNet"),
    ("Hone", None),
])
def test_names_do_not_match_when_unrelated_or_too_short(subnet_name, coin_name):
    assert not names_match(subnet_name, coin_name)


def test_tao_placeholder_is_detected():
    assert is_tao_placeholder(fixture("coingecko_tao_placeholder.png"))


def test_rescaled_tao_placeholder_is_detected():
    small = Image.open(io.BytesIO(fixture("coingecko_tao_placeholder.png"))).resize((96, 96))
    out = io.BytesIO()
    small.save(out, "PNG")
    assert is_tao_placeholder(update_subnets.normalize(out.getvalue()))


def test_real_logo_is_not_a_placeholder():
    assert not is_tao_placeholder(fixture("real_logo.png"))
    assert not is_tao_placeholder(update_subnets.normalize(png_bytes((255, 0, 0, 255))))


def test_fetch_logo_accepts_the_placeholder_from_a_stale_listing(monkeypatch):
    monkeypatch.setattr(update_subnets, "download", lambda url: fixture("coingecko_tao_placeholder.png"))

    assert isinstance(fetch_logo([LogoCandidate("coingecko", "https://cg/73.png", placeholder_only=True)]), bytes)


def test_fetch_logo_rejects_a_real_logo_from_a_stale_listing(monkeypatch):
    monkeypatch.setattr(update_subnets, "download", lambda url: fixture("real_logo.png"))

    outcome = fetch_logo([LogoCandidate("coingecko", "https://cg/5.png", placeholder_only=True)])

    assert outcome == (
        "coingecko https://cg/5.png: LogoError: listed under another name, only the TAO placeholder is taken from it"
    )


def test_fetch_logo_accepts_a_real_logo_from_a_matching_listing(monkeypatch):
    monkeypatch.setattr(update_subnets, "download", lambda url: fixture("real_logo.png"))

    assert isinstance(fetch_logo([LogoCandidate("coingecko", "https://cg/61.png")]), bytes)


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
