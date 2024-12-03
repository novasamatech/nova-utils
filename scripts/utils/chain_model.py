from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Union, Callable, TypeVar

from scalecodec import ScaleBytes

from .substrate_interface import create_connection_by_url
from .metadata_interaction import get_properties

from substrateinterface import SubstrateInterface

T = TypeVar('T')


class Chain():
    substrate: SubstrateInterface | None

    assets: List[ChainAsset]

    _type_registry: dict

    _type_cache: dict = {}

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

    def create_connection(self) -> SubstrateInterface:
        for node in self.nodes:
            try:
                print("Connecting to ", node.get('url'))
                self.substrate = create_connection_by_url(node.get('url'), type_registry=self._type_registry)
                print("Connected to ", node.get('url'))
                return self.substrate
                # if self.substrate.websocket.connected is True:
                #     return self.substrate
                # print(f"Can't connect to endpoint {node.get('url')} for the {self.name}")
            except:
                print("Can't connect to that node")
                continue

        print("Can't connect to all nodes of network", self.name)

    def recreate_connection(self) -> SubstrateInterface:
        if self.substrate is None:
            raise Exception("No connection was created before")

        for node in self.nodes:
            try:
                print("Connecting to ", node.get('url'))
                self.substrate.url = node.get('url')
                self.substrate.connect_websocket()
                print("Connected to ", node.get('url'))
                return self.substrate
                # if self.substrate.websocket.connected is True:
                #     return self.substrate
                # print(f"Can't connect to endpoint {node.get('url')} for the {self.name}")
            except:
                print("Can't connect to that node")
                continue

        print("Can't connect to all nodes of network", self.name)

    def close_substrate_connection(self):
        self.substrate.close()

    def init_properties(self):
        if (self.properties):
            return self.substrate
        self.properties = get_properties(self.substrate)

    def has_evm_addresses(self):
        return self.options is not None and "ethereumBased" in self.options

    def get_asset(self, symbol: str) -> ChainAsset:
        return next((a for a in self.assets if a.symbol == symbol))

    def access_substrate(self, action: Callable[[SubstrateInterface], T]) -> T:
        if self.substrate is None:
            self.create_connection()

        try:
            return action(self.substrate)
        except Exception as e:
            print("Attempting to re-create connection after receiving error", e)
            # try re-connecting socket and performing action once again
            self.recreate_connection()
            return action(self.substrate)


class ChainAsset:
    _data: dict

    symbol: str
    type: AssetType
    precision: int

    def __init__(self, data: dict, chain: Chain, chain_cache: dict):
        self._data = data

        self.symbol = data["symbol"]
        self.type = self._construct_type(data, chain, chain_cache)
        self.precision = data["precision"]

    # Backward-compatible override for code that still thinks this is a dict
    def __getitem__(self, item):
        return self._data[item]

    def unified_symbol(self) -> str:
        return self.symbol.removeprefix("xc")

    def planks(self, amount: int | float) -> int:
        return amount * 10**self.precision

    @staticmethod
    def _construct_type(data: dict, chain: Chain, chain_cache: dict) -> AssetType:
        type_label = data.get("type", "native")
        type_extras = data.get("typeExtras", {})

        match type_label:
            case "native":
                return NativeAssetType()
            case "statemine":
                return StatemineAssetType(type_extras)
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

    def __init__(self, type_extras: dict):
        self._pallet_name = type_extras.get("palletName", "Assets")
        self._asset_id = type_extras["assetId"]

    def pallet_name(self) -> str:
        return self._pallet_name

    def encodable_asset_id(self) -> object | None:
        if self._asset_id.startswith("0x"):
            return ScaleBytes(self._asset_id)
        else:
            return int(self._asset_id)


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
