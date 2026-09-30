import pytest

from scripts.bittensor.chain_source import Subnet
from scripts.bittensor.update_subnets import UpdateAborted, logo_filename, logo_url, merge

PNG_A = b"png-a"
PNG_B = b"png-b"


def subnet(netuid, logo_url_=None, name="Name", symbol="α"):
    return Subnet(netuid=netuid, name=name, symbol=symbol, logo_url=logo_url_)


def entry(netuid, logo, name="Name", symbol="α"):
    return {"netuid": netuid, "name": name, "symbol": symbol, "logo": logo}


def test_new_logo_is_written_and_referenced():
    result = merge([], [subnet(1, "https://x/a.png")], {1: PNG_A}, [])
    filename = logo_filename(1, PNG_A)
    assert result.entries == [entry(1, logo_url(filename))]
    assert result.files_to_write == {filename: PNG_A}
    assert result.files_to_delete == []


def test_unchanged_logo_writes_and_deletes_nothing():
    filename = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(filename))], [subnet(1, "https://x/a.png")], {1: PNG_A}, [filename])
    assert result.files_to_write == {}
    assert result.files_to_delete == []


def test_changed_logo_replaces_old_file():
    old, new = logo_filename(1, PNG_A), logo_filename(1, PNG_B)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: PNG_B}, [old])
    assert result.entries == [entry(1, logo_url(new))]
    assert result.files_to_write == {new: PNG_B}
    assert result.files_to_delete == [old]


def test_failed_download_keeps_previous_logo():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: "HTTPError: 404"}, [old])
    assert result.entries == [entry(1, logo_url(old))]
    assert result.files_to_delete == []
    assert result.kept_previous == {1: "HTTPError: 404"}


def test_failed_download_without_previous_gives_null():
    result = merge([], [subnet(1, "https://x/a.png")], {1: "LogoError: html"}, [])
    assert result.entries == [entry(1, None)]
    assert result.missing == {1: "LogoError: html"}


def test_previous_logo_whose_file_is_gone_is_not_kept():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: "timeout"}, [])
    assert result.entries == [entry(1, None)]


def test_logo_removed_on_chain_gives_null_and_deletes_file():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, None)], {}, [old])
    assert result.entries == [entry(1, None)]
    assert result.files_to_delete == [old]
    assert result.missing == {}


def test_entries_sorted_and_carry_name_and_symbol():
    result = merge([], [subnet(2, name=None, symbol="β"), subnet(0, symbol="Τ")], {}, [])
    assert result.entries == [entry(0, None, symbol="Τ"), entry(2, None, name=None, symbol="β")]


def test_aborts_when_chain_returns_less_than_half():
    previous = [entry(n, None) for n in range(10)]
    with pytest.raises(UpdateAborted):
        merge(previous, [subnet(n) for n in range(4)], {}, [])


def test_half_is_accepted():
    previous = [entry(n, None) for n in range(10)]
    assert len(merge(previous, [subnet(n) for n in range(5)], {}, []).entries) == 5
