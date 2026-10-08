"""Regenerate the subnets of bittensor/v1/config.json and icons/bittensor/subnets/ from Bittensor chain state.

Every other key of config.json, such as swapFee, is maintained by hand and kept as it is.

Run from the repo root: `make update-bittensor-subnets`.
"""
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

import requests

from scripts.bittensor.chain_source import ChainSourceError, Subnet, bittensor_node_urls, fetch_subnets
from scripts.bittensor.logo_normalizer import LogoError, normalize
from scripts.bittensor.price_source import PriceSourceError, fetch_price_ids

CONFIG_JSON = "bittensor/v1/config.json"
LOGO_DIR = "icons/bittensor/subnets"
LOGO_BASE_URL = f"https://raw.githubusercontent.com/novasamatech/nova-utils/master/{LOGO_DIR}"
DOWNLOAD_TIMEOUT = 15
MAX_LOGO_BYTES = 5 * 1024 * 1024
DOWNLOAD_WORKERS = 16
USER_AGENT = "Mozilla/5.0 (compatible; nova-utils-subnet-metadata)"

# Per netuid: normalised PNG bytes on success, a human-readable reason on failure.
LogoOutcome = Union[bytes, str]


class UpdateAborted(Exception):
    pass


@dataclass
class MergeResult:
    entries: List[dict]
    files_to_write: Dict[str, bytes]
    files_to_delete: List[str]
    kept_previous: Dict[int, str] = field(default_factory=dict)
    missing: Dict[int, str] = field(default_factory=dict)


def logo_filename(netuid: int, png: bytes) -> str:
    return f"sn{netuid}-{hashlib.sha256(png).hexdigest()[:8]}.png"


def logo_url(filename: str) -> str:
    return f"{LOGO_BASE_URL}/{filename}"


def _filename(url: str) -> str:
    return url.rsplit("/", 1)[-1]


def merge(
    previous: List[dict],
    subnets: List[Subnet],
    logos: Dict[int, LogoOutcome],
    existing_files: List[str],
    price_ids: Optional[Dict[int, str]],
) -> MergeResult:
    """`price_ids` is None when the price source was unavailable: previous priceIds are kept then."""
    if previous and len(subnets) < len(previous) / 2:
        raise UpdateAborted(f"chain returned {len(subnets)} subnets, current file has {len(previous)}")

    previous_logo = {
        e["netuid"]: e["logo"] for e in previous
        if e.get("logo") and _filename(e["logo"]) in existing_files
    }
    if price_ids is None:
        price_ids = {e["netuid"]: e["priceId"] for e in previous if e.get("priceId")}
    result = MergeResult(entries=[], files_to_write={}, files_to_delete=[])

    for subnet in sorted(subnets, key=lambda s: s.netuid):
        outcome = logos.get(subnet.netuid)
        logo: Optional[str] = None
        if isinstance(outcome, bytes):
            filename = logo_filename(subnet.netuid, outcome)
            logo = logo_url(filename)
            if filename not in existing_files:
                result.files_to_write[filename] = outcome
        elif subnet.logo_url and subnet.netuid in previous_logo:
            logo = previous_logo[subnet.netuid]
            result.kept_previous[subnet.netuid] = outcome
        elif subnet.logo_url:
            result.missing[subnet.netuid] = outcome

        result.entries.append({
            "netuid": subnet.netuid,
            "name": subnet.name,
            "symbol": subnet.symbol,
            "priceId": price_ids.get(subnet.netuid),
            "logo": logo,
        })

    referenced = {_filename(e["logo"]) for e in result.entries if e["logo"]}
    result.files_to_delete = sorted(f for f in existing_files if f not in referenced)
    return result


def download(url: str) -> bytes:
    with requests.get(url, timeout=DOWNLOAD_TIMEOUT, headers={"User-Agent": USER_AGENT}, stream=True) as response:
        response.raise_for_status()
        chunks, size = [], 0
        for chunk in response.iter_content(64 * 1024):
            size += len(chunk)
            if size > MAX_LOGO_BYTES:
                raise LogoError(f"larger than {MAX_LOGO_BYTES} bytes")
            chunks.append(chunk)
    return b"".join(chunks)


def fetch_logo(subnet: Subnet) -> LogoOutcome:
    try:
        return normalize(download(subnet.logo_url))
    except (requests.RequestException, LogoError) as e:
        return f"{type(e).__name__}: {e}"


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def with_subnets(config: dict, entries: List[dict]) -> dict:
    return {**config, "subnets": entries}


def write_config(path: str, config: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")


def existing_logo_files(directory: str) -> List[str]:
    if not os.path.isdir(directory):
        return []
    return sorted(f for f in os.listdir(directory) if f.endswith(".png"))


def main() -> None:
    config = load_config(CONFIG_JSON)
    previous = config.get("subnets", [])
    subnets = fetch_subnets(bittensor_node_urls())

    with_logo = [s for s in subnets if s.logo_url]
    with ThreadPoolExecutor(DOWNLOAD_WORKERS) as pool:
        logos = dict(zip((s.netuid for s in with_logo), pool.map(fetch_logo, with_logo)))

    try:
        price_ids = fetch_price_ids()
    except PriceSourceError as e:
        print(f"Price source unavailable, keeping previous priceIds: {e}", file=sys.stderr)
        price_ids = None

    result = merge(previous, subnets, logos, existing_logo_files(LOGO_DIR), price_ids)

    os.makedirs(LOGO_DIR, exist_ok=True)
    for filename, png in result.files_to_write.items():
        with open(os.path.join(LOGO_DIR, filename), "wb") as f:
            f.write(png)
    for filename in result.files_to_delete:
        os.remove(os.path.join(LOGO_DIR, filename))
    write_config(CONFIG_JSON, with_subnets(config, result.entries))

    with_logos = sum(1 for e in result.entries if e["logo"])
    with_prices = sum(1 for e in result.entries if e["priceId"])
    print(f"{len(result.entries)} subnets, {with_logos} with logo, {with_prices} with priceId; "
          f"{len(result.files_to_write)} logos written, {len(result.files_to_delete)} deleted")
    for title, failures in (("Kept previous logo", result.kept_previous), ("No logo", result.missing)):
        for netuid, reason in sorted(failures.items()):
            print(f"  {title} for SN{netuid}: {reason}")


if __name__ == "__main__":
    try:
        main()
    except (ChainSourceError, UpdateAborted) as e:
        print(f"Aborted: {e}", file=sys.stderr)
        sys.exit(1)
