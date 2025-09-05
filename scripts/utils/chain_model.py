from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import List, Callable, TypeVar, Tuple

from scalecodec import ScaleBytes
from substrateinterface import SubstrateInterface

from .metadata_interaction import get_properties
from .substrate_interface import create_connection_by_url
from ..xcm_transfers.utils.log import debug_log

T = TypeVar('T')

ChainId = str
ChainAssetId = int

FullChainAssetId = (ChainId, ChainAssetId)


class Chain:
    substrate: SubstrateInterface | None

    assets: List[ChainAsset]

    _type_registry: dict

    _type_cache: dict = {}

    _access_substrate_counter: int = 0

    def __init__(self, arg, type_registry=None):
        self.chainId = arg.get("chainId")
        self.parentId = arg.get("parentId")
        self.name = arg.get("name")
        self.assets = [ChainAsset(data, self, self._type_cache) for data in arg.get("assets")]
        self.nodes = arg.get("nodes")
        self.explorers = arg.get("explorers")
        self.addressPrefix = arg.get("addressPrefix")
        self.externalApi = arg.get("externalApi")
        self.options = arg.get("options")
        self.substrate = None
        self.properties = None

        self._type_registry = type_registry

    @staticmethod
    def latest_config_version():
        return os.getenv('CHAINS_VERSION', default="v22")

    def create_connection(self) -> SubstrateInterface:
        def create_node_connection(node_url: str):
            self.substrate = create_connection_by_url(node_url, type_registry=self._type_registry)

        self._try_connect_over_all_nodes(create_node_connection)

        return self.substrate

    def recreate_connection(self) -> SubstrateInterface:
        if self.substrate is None:
            raise Exception("No connection was created before")

        def recreate_node_connection(node_url: str):
            self.substrate.url = node_url
            self.substrate.connect_websocket()

        self._try_connect_over_all_nodes(recreate_node_connection)

        return self.substrate

    def _try_connect_over_all_nodes(self, connect_to_node: Callable[[str], None]):
        for node in self.nodes:
            node_url = node.get('url')

            try:
                print("Connecting to ", node_url)
                connect_to_node(node_url)
                print("Connected to ", node_url)
                return
            except:
                print("Can't connect to", node_url)
                continue

        raise Exception("Can't connect to all nodes of network")

    def close_substrate_connection(self):
        self.substrate.close()
        self.substrate = None

    def init_properties(self):
        if (self.properties):
            return self.substrate
        self.properties = get_properties(self.substrate)

    def has_evm_addresses(self):
        return self.options is not None and "ethereumBased" in self.options

    def get_asset_by_symbol(self, symbol: str) -> ChainAsset:
        return next((a for a in self.assets if a.symbol == symbol))

    def get_asset_by_id(self, id: int) -> ChainAsset:
        return next((a for a in self.assets if a.id == id))

    def get_utility_asset(self) -> ChainAsset:
        return self.get_asset_by_id(0)

    def access_substrate(self, action: Callable[[SubstrateInterface], T]) -> T:
        if self.substrate is None:
            self.create_connection()

        try:
            self._access_substrate_counter += 1
            return action(self.substrate)
        except Exception as e:
            if self._access_substrate_counter == 1:
                print("Attempting to re-create connection after broken connection:", e)
                # try re-connecting socket and performing action once again
                self.recreate_connection()
                return action(self.substrate)
            else:
                debug_log("Nested access_substrate - propagate error to the outer-most level")
                raise e
        finally:
            self._access_substrate_counter -= 1

    def encodable_address(self, account_id: str):
        if self.has_evm_addresses():
            return account_id
        elif self._uses_multi_address():
            return {"Id": account_id }
        else:
            return account_id

    def _uses_multi_address(self) -> bool:
        type_def = self.substrate.get_type_definition("Address")
        return type_def is dict

class ChainAsset:
    _data: dict

    symbol: str
    type: AssetType
    precision: int

    id: ChainAssetId

    chain: Chain

    def __init__(self, data: dict, chain: Chain, chain_cache: dict):
        self._data = data

        self.id = data["assetId"]
        self.symbol = data["symbol"]
        self.type = self._construct_type(data, chain, chain_cache)
        self.precision = data["precision"]
        self.chain = chain

    # Backward-compatible override for code that still thinks this is a dict
    def __getitem__(self, item):
        return self._data[item]

    def unified_symbol(self) -> str:
        return self.symbol.removeprefix("xc")

    def planks(self, amount: int | float) -> int:
        return int(amount * 10 ** self.precision)

    def amount(self, planks: int) -> float:
        return planks / 10 ** self.precision

    def full_chain_asset_id(self) -> Tuple[str, int]:
        return self.chain.chainId, self.id

    @staticmethod
    def _construct_type(data: dict, chain: Chain, chain_cache: dict) -> AssetType:
        type_label = data.get("type", "native")
        type_extras = data.get("typeExtras", {})

        match type_label:
            case "native":
                return NativeAssetType()
            case "statemine":
                return StatemineAssetType(type_extras, chain)
            case "orml":
                return OrmlAssetType(type_extras, chain, chain_cache)
            case _:
                return UnsupportedAssetType()


class AssetType(ABC):

    @abstractmethod
    def encodable_asset_id(self) -> object | None:
        pass


class NativeAssetType(AssetType):

    def encodable_asset_id(self):
        return None


class UnsupportedAssetType(AssetType):

    def encodable_asset_id(self) -> object | None:
        raise Exception("Unsupported")


class StatemineAssetType(AssetType):
    _pallet_name: str
    _asset_id: str

    _chain: Chain

    def __init__(self, type_extras: dict, chain: Chain):
        self._pallet_name = type_extras.get("palletName", "Assets")
        self._asset_id = type_extras["assetId"]

        self._chain = chain

    def pallet_name(self) -> str:
        return self._pallet_name

    def encodable_asset_id(self) -> object | None:
        if self._asset_id.startswith("0x"):
            return self._chain.access_substrate(self._encodable_id_from_hex)
        else:
            return int(self._asset_id)

    def _encodable_id_from_hex(self, substrate: SubstrateInterface):
        type_index = substrate.get_metadata_call_function(self._pallet_name, "transfer").args[0]["type"].value
        type_name = "scale_info::" + str(type_index)
        asset_id_bytes = ScaleBytes(self._asset_id)
        return substrate.create_scale_object(type_name, asset_id_bytes).process()


_orml_pallet_candidates = ["Tokens", "Currencies"]
_orml_pallet_cache_key = "orml_pallet_name"


class OrmlAssetType(AssetType):
    _asset_id: str
    _asset_type_scale: str

    _chain: Chain

    _chain_cache: dict

    def __init__(self, type_extras: dict, chain: Chain, chain_cache: dict):
        self._asset_id = type_extras["currencyIdScale"]
        self._asset_type_scale = type_extras["currencyIdType"].replace(".", "::")
        self._chain = chain
        self._chain_cache = chain_cache

    def encodable_asset_id(self) -> object | None:
        return self._chain.access_substrate(
            lambda s: self.__create_encodable_id(s)
        )

    def __create_encodable_id(self, substrate: SubstrateInterface):
        encoded_bytes = ScaleBytes(self._asset_id)

        return substrate.create_scale_object(self._asset_type_scale, encoded_bytes).process()

    def pallet_name(self) -> str:
        if self._chain_cache.get(_orml_pallet_cache_key) is None:
            self._chain_cache[_orml_pallet_cache_key] = self.__determine_pallet_name()

        return self._chain_cache[_orml_pallet_cache_key]

    def __determine_pallet_name(self) -> str:
        return self._chain.access_substrate(
            lambda s: self.__determine_pallet_name_using_connection(s)
        )

    @staticmethod
    def __determine_pallet_name_using_connection(substrate: SubstrateInterface) -> str:
        for candidate in _orml_pallet_candidates:
            module = substrate.get_metadata_module(candidate)
            if module is not None:
                return candidate

        raise Exception(f"Failed to find orml pallet name, searched for {_orml_pallet_candidates}")
