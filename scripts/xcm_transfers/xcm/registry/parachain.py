from dataclasses import dataclass

from scripts.utils.chain_model import Chain


@dataclass
class Parachain:
    parachain_id: int
    chain: Chain