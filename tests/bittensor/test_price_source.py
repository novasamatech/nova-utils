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


def coin_with_image(coin_id, symbol, image, name=None):
    return {**coin(coin_id, symbol), "name": name or coin_id, "image": image}


def test_logos_from_coins_carry_name_and_image_by_netuid():
    from scripts.bittensor.price_source import CoinGeckoLogo, logos_from_coins

    coins = [coin_with_image("synth-2", "sn50", "https://coin-images.coingecko.com/x/sn50.png?1", name="Synth")]
    assert logos_from_coins(coins) == {50: CoinGeckoLogo(name="Synth", url="https://coin-images.coingecko.com/x/sn50.png?1")}


def test_logos_skip_coins_without_https_image():
    from scripts.bittensor.price_source import logos_from_coins

    coins = [coin("a", "sn1"), coin_with_image("b", "sn2", None), coin_with_image("c", "sn3", "http://x/y.png")]
    assert logos_from_coins(coins) == {}


def test_logos_drop_ambiguous_netuid_like_price_ids():
    from scripts.bittensor.price_source import logos_from_coins

    coins = [coin_with_image("a", "sn5", "https://x/a.png"), coin_with_image("b", "sn5", "https://x/b.png")]
    assert logos_from_coins(coins) == {}
