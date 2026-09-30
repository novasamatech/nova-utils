import re
from collections import defaultdict
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


def price_ids_from_coins(coins: List[dict]) -> Dict[int, str]:
    by_netuid = defaultdict(set)
    for coin in coins:
        match = _SUBNET_SYMBOL.fullmatch(coin["symbol"].lower())
        if match:
            by_netuid[int(match.group(1))].add(coin["id"])

    # Two coins claiming one netuid cannot be told apart safely, so neither is used.
    price_ids = {netuid: ids.pop() for netuid, ids in by_netuid.items() if len(ids) == 1}
    price_ids[0] = ROOT_PRICE_ID
    return price_ids


def fetch_price_ids() -> Dict[int, str]:
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
    return price_ids_from_coins(coins)
