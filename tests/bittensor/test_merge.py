import io

import pytest
from PIL import Image

from scripts.bittensor.chain_source import Subnet
from scripts.bittensor.update_subnets import UpdateAborted, logo_filename, logo_url, merge, with_subnets


def _png(color, compress_level=9):
    out = io.BytesIO()
    Image.new("RGBA", (4, 4), color).save(out, "PNG", compress_level=compress_level)
    return out.getvalue()


PNG_A = _png((255, 0, 0, 255))
PNG_B = _png((0, 0, 255, 255))


def subnet(netuid, logo_url_=None, name="Name", symbol="α"):
    return Subnet(netuid=netuid, name=name, symbol=symbol, logo_url=logo_url_)


def entry(netuid, logo, name="Name", symbol="α", price_id=None):
    return {"netuid": netuid, "name": name, "symbol": symbol, "priceId": price_id, "logo": logo}


def test_new_logo_is_written_and_referenced():
    result = merge([], [subnet(1, "https://x/a.png")], {1: PNG_A}, [], {})
    filename = logo_filename(1, PNG_A)
    assert result.entries == [entry(1, logo_url(filename))]
    assert result.files_to_write == {filename: PNG_A}
    assert result.files_to_delete == []


def test_unchanged_logo_writes_and_deletes_nothing():
    filename = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(filename))], [subnet(1, "https://x/a.png")], {1: PNG_A}, [filename], {})
    assert result.files_to_write == {}
    assert result.files_to_delete == []


def test_changed_logo_replaces_old_file():
    old, new = logo_filename(1, PNG_A), logo_filename(1, PNG_B)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: PNG_B}, [old], {})
    assert result.entries == [entry(1, logo_url(new))]
    assert result.files_to_write == {new: PNG_B}
    assert result.files_to_delete == [old]


def test_failed_download_keeps_previous_logo():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: "HTTPError: 404"}, [old], {})
    assert result.entries == [entry(1, logo_url(old))]
    assert result.files_to_delete == []
    assert result.kept_previous == {1: "HTTPError: 404"}


def test_failed_download_without_previous_gives_null():
    result = merge([], [subnet(1, "https://x/a.png")], {1: "LogoError: html"}, [], {})
    assert result.entries == [entry(1, None)]
    assert result.missing == {1: "LogoError: html"}


def test_previous_logo_whose_file_is_gone_is_not_kept():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: "timeout"}, [], {})
    assert result.entries == [entry(1, None)]


def test_logo_removed_on_chain_gives_null_and_deletes_file():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, None)], {}, [old], {})
    assert result.entries == [entry(1, None)]
    assert result.files_to_delete == [old]
    assert result.missing == {}


def test_entries_sorted_and_carry_name_and_symbol():
    result = merge([], [subnet(2, name=None, symbol="β"), subnet(0, symbol="Τ")], {}, [], {})
    assert result.entries == [entry(0, None, symbol="Τ"), entry(2, None, name=None, symbol="β")]


def test_aborts_when_chain_returns_less_than_half():
    previous = [entry(n, None) for n in range(10)]
    with pytest.raises(UpdateAborted):
        merge(previous, [subnet(n) for n in range(4)], {}, [], {})


def test_half_is_accepted():
    previous = [entry(n, None) for n in range(10)]
    assert len(merge(previous, [subnet(n) for n in range(5)], {}, [], {}).entries) == 5


def test_price_id_is_attached_by_netuid():
    result = merge([], [subnet(0, symbol="Τ"), subnet(64)], {}, [], {0: "bittensor", 64: "chutes"})
    assert result.entries == [entry(0, None, symbol="Τ", price_id="bittensor"), entry(64, None, price_id="chutes")]


def test_subnet_unknown_to_price_source_gets_null_price_id():
    result = merge([entry(7, None, price_id="old")], [subnet(7)], {}, [], {0: "bittensor"})
    assert result.entries == [entry(7, None)]


def test_unavailable_price_source_keeps_previous_price_ids():
    result = merge([entry(7, None, price_id="subvortex")], [subnet(7), subnet(8)], {}, [], None)
    assert result.entries == [entry(7, None, price_id="subvortex"), entry(8, None)]


def test_regenerated_config_keeps_swap_fee():
    config = {"swapFee": 0.003, "subnets": [entry(1, None)]}
    assert with_subnets(config, [entry(2, None)]) == {"swapFee": 0.003, "subnets": [entry(2, None)]}


def test_logo_from_fallback_source_is_used_without_chain_logo_url():
    result = merge([], [subnet(1)], {1: PNG_A}, [], {})
    filename = logo_filename(1, PNG_A)
    assert result.entries == [entry(1, logo_url(filename))]
    assert result.files_to_write == {filename: PNG_A}


def test_failed_fallback_keeps_previous_logo_without_chain_logo_url():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1)], {1: "coingecko https://cg/1.png: HTTPError: 404"}, [old], {})
    assert result.entries == [entry(1, logo_url(old))]
    assert result.kept_previous == {1: "coingecko https://cg/1.png: HTTPError: 404"}


def test_report_lists_counts_and_failures():
    from scripts.bittensor.update_subnets import MergeResult, report

    result = MergeResult(
        entries=[entry(1, "https://x/sn1-a.png", price_id="a"), entry(2, None)],
        files_to_write={"sn1-a.png": PNG_A},
        files_to_delete=["sn1-old.png"],
        kept_previous={1: "chain https://c/1.png: HTTPError: 500"},
        missing={2: "coingecko https://cg/2.png: LogoError: html"},
    )
    assert report(result) == (
        "2 subnets, 1 with logo, 1 with priceId; 1 logos written, 1 deleted\n"
        "\n"
        "Kept previous logo for SN1: chain https://c/1.png: HTTPError: 500\n"
        "No logo for SN2: coingecko https://cg/2.png: LogoError: html"
    )


def test_logo_filename_depends_on_pixels_not_on_png_encoding():
    fast, small = _png((255, 0, 0, 255), 0), _png((255, 0, 0, 255), 9)
    assert fast != small
    assert logo_filename(1, fast) == logo_filename(1, small)


def test_logo_filename_differs_for_different_pixels():
    assert logo_filename(1, PNG_A) != logo_filename(1, PNG_B)
