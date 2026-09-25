import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from substrateinterface import SubstrateInterface

from scripts.utils.chain_model import Chain

BITTENSOR_CHAIN_ID = "2f0555cc76fc2840a25a6ea3b9637146806f1f44b090c175ffde2a7e5ab36c03"
PALLET = "SubtensorModule"


@dataclass(frozen=True)
class Subnet:
    netuid: int
    name: Optional[str]
    symbol: str
    logo_url: Optional[str]


class ChainSourceError(Exception):
    pass


def bittensor_node_urls(chains_path: Optional[str] = None) -> List[str]:
    path = chains_path or f"chains/{Chain.latest_config_version()}/chains.json"
    with open(path, encoding="utf-8") as f:
        chains = json.load(f)
    for chain in chains:
        if chain["chainId"] == BITTENSOR_CHAIN_ID:
            return [node["url"] for node in chain["nodes"]]
    raise ChainSourceError(f"Bittensor chain not found in {path}")


def _text(value) -> Optional[str]:
    """Vec<u8> fields decode as str when valid UTF-8; fall back to decoding a hex string."""
    if not value:
        return None
    if value.startswith("0x"):
        try:
            value = bytes.fromhex(value[2:]).decode("utf-8")
        except ValueError:
            pass
    return value.strip() or None


def subnets_from_storage(
    networks_added: Dict[int, bool],
    identities: Dict[int, dict],
    symbols: Dict[int, str],
) -> List[Subnet]:
    subnets = []
    for netuid in sorted(n for n, added in networks_added.items() if added):
        identity = identities.get(netuid) or {}
        subnets.append(Subnet(
            netuid=netuid,
            name=_text(identity.get("subnet_name")),
            symbol=_text(symbols.get(netuid)) or "",
            logo_url=_text(identity.get("logo_url")),
        ))
    return subnets


def _query_map(substrate: SubstrateInterface, storage: str) -> dict:
    return {int(key.value): value.value for key, value in substrate.query_map(PALLET, storage, page_size=1000)}


def fetch_subnets(node_urls: List[str]) -> List[Subnet]:
    errors = []
    for url in node_urls:
        substrate = None
        try:
            substrate = SubstrateInterface(url=url)
            return subnets_from_storage(
                _query_map(substrate, "NetworksAdded"),
                _query_map(substrate, "SubnetIdentitiesV3"),
                _query_map(substrate, "TokenSymbol"),
            )
        except Exception as e:
            errors.append(f"{url}: {e!r}")
        finally:
            if substrate is not None:
                substrate.close()
    raise ChainSourceError("No Bittensor node answered: " + "; ".join(errors))
