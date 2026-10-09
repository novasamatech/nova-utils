import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

import requests

# CoinGecko lists every subnet alpha token in this category under the symbol `sn<netuid>`.
CATEGORY_URL = "https://api.coingecko.com/api/v3/coins/markets"
CATEGORY = "bittensor-subnets"
PAGE_SIZE = 250
TIMEOUT = 30
ROOT_PRICE_ID = "bittensor"

_SUBNET_SYMBOL = re.compile(r"sn(\d+)")


class PriceSourceError(Exception):
    pass


@dataclass(frozen=True)
class CoinGeckoLogo:
    name: str
    url: str


def _coins_by_netuid(coins: List[dict]) -> Dict[int, dict]:
    by_netuid = defaultdict(list)
    for coin in coins:
        match = _SUBNET_SYMBOL.fullmatch(coin["symbol"].lower())
        if match:
            by_netuid[int(match.group(1))].append(coin)

    # Two coins claiming one netuid cannot be told apart safely, so neither is used.
    return {netuid: found[0] for netuid, found in by_netuid.items() if len(found) == 1}


def price_ids_from_coins(coins: List[dict]) -> Dict[int, str]:
    price_ids = {netuid: coin["id"] for netuid, coin in _coins_by_netuid(coins).items()}
    price_ids[0] = ROOT_PRICE_ID
    return price_ids


def logos_from_coins(coins: List[dict]) -> Dict[int, CoinGeckoLogo]:
    """The CoinGecko coin image, a fallback for subnets without a usable on-chain logo. The coin name
    comes along so that callers can tell a stale listing of a renamed subnet from a current one."""
    return {
        netuid: CoinGeckoLogo(name=coin.get("name") or "", url=coin["image"])
        for netuid, coin in _coins_by_netuid(coins).items()
        if isinstance(coin.get("image"), str) and coin["image"].startswith("https://")
    }


def fetch_coins() -> List[dict]:
    """Every coin of the CoinGecko subnet category, or PriceSourceError when CoinGecko is unavailable."""
    coins, page = [], 1
    try:
        while True:
            response = requests.get(CATEGORY_URL, timeout=TIMEOUT, params={
                "vs_currency": "usd", "category": CATEGORY, "per_page": PAGE_SIZE, "page": page,
            })
            response.raise_for_status()
            batch = response.json()
            coins.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
            page += 1
    except (requests.RequestException, ValueError) as e:
        raise PriceSourceError(f"{type(e).__name__}: {e}") from e
    if not coins:
        raise PriceSourceError(f"CoinGecko category {CATEGORY} is empty")
    return coins
