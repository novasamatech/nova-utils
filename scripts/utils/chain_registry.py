from __future__ import annotations

from typing import Dict, List

from scripts.utils.chain_model import Chain, ChainId
from scripts.utils.work_with_data import get_data_from_file


class ChainRegistry:
    _chains: Dict[ChainId, Chain]

    def __init__(self, chains: List[Chain]):
        self._chains = {chain.chainId: chain for chain in chains}

    def get_chain(self, chain_id: ChainId) -> Chain:
        return self._chains[chain_id]

    def polkadot(self) -> Chain:
        return self.get_chain("91b171bb158e2d3848fa23a9f1c25182fb8e20313b2c1eb49219da7a70ce90c3")

    @staticmethod
    def create_from_config(config_path: str) -> ChainRegistry:
        config_data = get_data_from_file(config_path)
        chains = [Chain(chain_config) for chain_config in config_data]
        return ChainRegistry(chains)

    @staticmethod
    def create_latest_prod():
        path = "../chains/v21/chains.json"
        return ChainRegistry.create_from_config(path)
