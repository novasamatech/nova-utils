from scripts.bittensor.price_source import ROOT_PRICE_ID, price_ids_from_coins


def coin(coin_id, symbol):
    return {"id": coin_id, "symbol": symbol, "name": coin_id}


def test_subnet_symbol_maps_to_netuid():
    assert price_ids_from_coins([coin("chutes", "sn64"), coin("apex-5", "SN1")]) == {
        0: ROOT_PRICE_ID, 64: "chutes", 1: "apex-5",
    }


def test_root_netuid_is_tao():
    assert price_ids_from_coins([]) == {0: "bittensor"}


def test_coins_without_subnet_symbol_are_ignored():
    assert price_ids_from_coins([coin("acore-ai-token", "acore"), coin("x", "sn")]) == {0: ROOT_PRICE_ID}


def test_ambiguous_netuid_is_dropped():
    assert price_ids_from_coins([coin("a", "sn5"), coin("b", "sn5"), coin("c", "sn6")]) == {
        0: ROOT_PRICE_ID, 6: "c",
    }
