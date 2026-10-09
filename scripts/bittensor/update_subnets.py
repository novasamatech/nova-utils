"""Regenerate the subnets of bittensor/v1/config.json and icons/bittensor/subnets/ from Bittensor chain state.

A subnet logo comes from the first source that yields an image: a hand-picked URL in
bittensor/v1/logo-overrides.json, the logo_url of the on-chain subnet identity, then the CoinGecko
coin image. A renamed subnet keeps the CoinGecko listing of its previous owner, so when the coin is
not named like the subnet only CoinGecko's generic TAO placeholder is taken from it, never the old
owner's logo. Every other key of config.json, such as swapFee, is maintained by hand and kept as it is.

Run from the repo root: `make update-bittensor-subnets`. Pass `--report FILE` to also write the
summary printed at the end to FILE, the daily workflow puts it into the pull request body.
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

import requests
from PIL import Image

from scripts.bittensor.chain_source import ChainSourceError, Subnet, bittensor_node_urls, fetch_subnets
from scripts.bittensor.logo_normalizer import LogoError, normalize
from scripts.bittensor.price_source import (
    CoinGeckoLogo, PriceSourceError, fetch_coins, logos_from_coins, price_ids_from_coins,
)

CONFIG_JSON = "bittensor/v1/config.json"
LOGO_OVERRIDES_JSON = "bittensor/v1/logo-overrides.json"
LOGO_DIR = "icons/bittensor/subnets"
LOGO_BASE_URL = f"https://raw.githubusercontent.com/novasamatech/nova-utils/master/{LOGO_DIR}"
DOWNLOAD_TIMEOUT = 15
MAX_LOGO_BYTES = 5 * 1024 * 1024
DOWNLOAD_WORKERS = 16
USER_AGENT = "Mozilla/5.0 (compatible; nova-utils-subnet-metadata)"

# Per netuid: normalised PNG bytes on success, a human-readable reason on failure.
LogoOutcome = Union[bytes, str]

# CoinGecko gives every subnet token without an own logo the TAO logo, recognised here by its
# perceptual hash (see dhash) so that a rescaled or re-encoded copy still matches.
TAO_LOGO_DHASH = 0x3000707010700010
TAO_LOGO_MAX_DISTANCE = 4
# A name shorter than this says too little to confirm that two listings are the same project.
MIN_NAME_LENGTH = 3

_NOT_ALNUM = re.compile(r"[^0-9a-z]+")


class UpdateAborted(Exception):
    pass


@dataclass(frozen=True)
class LogoCandidate:
    source: str
    url: str
    # The listing is not named like the subnet: its own logo may belong to a previous owner, so
    # only the generic TAO placeholder, which cannot be wrong, is accepted from it.
    placeholder_only: bool = False


LogoCandidates = List[LogoCandidate]


@dataclass
class MergeResult:
    entries: List[dict]
    files_to_write: Dict[str, bytes]
    files_to_delete: List[str]
    kept_previous: Dict[int, str] = field(default_factory=dict)
    missing: Dict[int, str] = field(default_factory=dict)


def logo_filename(netuid: int, png: bytes) -> str:
    """Named by the pixels, not the PNG bytes: zlib differs between platforms, so hashing the encoding
    would rename every logo whenever the generator runs on another machine."""
    with Image.open(io.BytesIO(png)) as img:
        pixels = img.convert("RGBA").tobytes()
    return f"sn{netuid}-{hashlib.sha256(pixels).hexdigest()[:8]}.png"


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
    """`logos` holds an outcome for every subnet that had at least one logo source; a subnet whose
    sources all failed keeps its previous logo. `price_ids` is None when the price source was
    unavailable: previous priceIds are kept then."""
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
        elif outcome is not None and subnet.netuid in previous_logo:
            logo = previous_logo[subnet.netuid]
            result.kept_previous[subnet.netuid] = outcome
        elif outcome is not None:
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


def dhash(png: bytes, size: int = 8) -> int:
    """Difference hash over a tiny grayscale copy, flattened onto white: the same picture at another
    size or encoding gives (nearly) the same bits, a different picture gives mostly different ones."""
    with Image.open(io.BytesIO(png)) as img:
        rgba = img.convert("RGBA")
        flat = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        flat.alpha_composite(rgba)
    gray = flat.convert("L").resize((size + 1, size), Image.LANCZOS)
    bits = 0
    for y in range(size):
        for x in range(size):
            bits = (bits << 1) | (gray.getpixel((x, y)) > gray.getpixel((x + 1, y)))
    return bits


def is_tao_placeholder(png: bytes) -> bool:
    return bin(dhash(png) ^ TAO_LOGO_DHASH).count("1") <= TAO_LOGO_MAX_DISTANCE


def fetch_logo(candidates: LogoCandidates) -> LogoOutcome:
    """The normalised logo of the first candidate that downloads and decodes, else why each one failed."""
    failures = []
    for candidate in candidates:
        try:
            png = normalize(download(candidate.url))
            if candidate.placeholder_only and not is_tao_placeholder(png):
                raise LogoError("listed under another name, only the TAO placeholder is taken from it")
            return png
        except (requests.RequestException, LogoError) as e:
            failures.append(f"{candidate.source} {candidate.url}: {type(e).__name__}: {e}")
    return "; ".join(failures)


def names_match(subnet_name: Optional[str], coin_name: Optional[str]) -> bool:
    """Whether a CoinGecko listing still describes the subnet: one normalised name contains the other."""
    first, second = (_NOT_ALNUM.sub("", (name or "").lower()) for name in (subnet_name, coin_name))
    if min(len(first), len(second)) < MIN_NAME_LENGTH:
        return False
    return first in second or second in first


def logo_candidates(
    subnets: List[Subnet], overrides: Dict[int, str], coingecko: Dict[int, CoinGeckoLogo],
) -> Dict[int, LogoCandidates]:
    candidates = {}
    for subnet in subnets:
        found = []
        if subnet.netuid in overrides:
            found.append(LogoCandidate("override", overrides[subnet.netuid]))
        if subnet.logo_url:
            found.append(LogoCandidate("chain", subnet.logo_url))
        coin = coingecko.get(subnet.netuid)
        if coin:
            found.append(LogoCandidate("coingecko", coin.url, placeholder_only=not names_match(subnet.name, coin.name)))
        if found:
            candidates[subnet.netuid] = found
    return candidates


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_logo_overrides(path: str) -> Dict[int, str]:
    """Hand-picked logo URLs keyed by netuid, for subnets whose on-chain and CoinGecko logos are wrong or absent."""
    overrides = load_config(path)
    for netuid, url in overrides.items():
        if not (isinstance(url, str) and url.startswith("https://")):
            raise ValueError(f"{path}: logo override for SN{netuid} must be an https URL, got {url!r}")
    return {int(netuid): url for netuid, url in overrides.items()}


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


def report(result: MergeResult) -> str:
    with_logos = sum(1 for e in result.entries if e["logo"])
    with_prices = sum(1 for e in result.entries if e["priceId"])
    lines = [
        f"{len(result.entries)} subnets, {with_logos} with logo, {with_prices} with priceId; "
        f"{len(result.files_to_write)} logos written, {len(result.files_to_delete)} deleted",
        "",
    ]
    for title, failures in (("Kept previous logo", result.kept_previous), ("No logo", result.missing)):
        lines.extend(f"{title} for SN{netuid}: {reason}" for netuid, reason in sorted(failures.items()))
    return "\n".join(lines).rstrip()


def main(report_path: Optional[str] = None) -> None:
    config = load_config(CONFIG_JSON)
    previous = config.get("subnets", [])
    overrides = load_logo_overrides(LOGO_OVERRIDES_JSON)
    subnets = fetch_subnets(bittensor_node_urls())

    try:
        coins = fetch_coins()
        price_ids, coingecko_logos = price_ids_from_coins(coins), logos_from_coins(coins)
    except PriceSourceError as e:
        print(f"CoinGecko unavailable, keeping previous priceIds and skipping CoinGecko logos: {e}", file=sys.stderr)
        price_ids, coingecko_logos = None, {}

    candidates = logo_candidates(subnets, overrides, coingecko_logos)
    with ThreadPoolExecutor(DOWNLOAD_WORKERS) as pool:
        logos = dict(zip(candidates, pool.map(fetch_logo, candidates.values())))

    result = merge(previous, subnets, logos, existing_logo_files(LOGO_DIR), price_ids)

    os.makedirs(LOGO_DIR, exist_ok=True)
    for filename, png in result.files_to_write.items():
        with open(os.path.join(LOGO_DIR, filename), "wb") as f:
            f.write(png)
    for filename in result.files_to_delete:
        os.remove(os.path.join(LOGO_DIR, filename))
    write_config(CONFIG_JSON, with_subnets(config, result.entries))

    summary = report(result)
    print(summary)
    if report_path:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(summary + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", metavar="FILE", help="also write the final summary to FILE")
    args = parser.parse_args()
    try:
        main(args.report)
    except (ChainSourceError, UpdateAborted, ValueError) as e:
        print(f"Aborted: {e}", file=sys.stderr)
        sys.exit(1)
