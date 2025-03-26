from dataclasses import dataclass
from typing import List

from scripts.utils.chain_model import ChainId
from scripts.xcm_transfers.xcm.registry.xcm_chain import ParachainId


@dataclass
class HrmpChannel:
    sender: ParachainId
    recipient: ParachainId

    def __init__(self, data: dict[str, int]):
        self.sender = data.get("sender")
        self.recipient = data.get("receiver")


HrmpChannelsByConsensus = dict[ChainId, List[HrmpChannel]]
