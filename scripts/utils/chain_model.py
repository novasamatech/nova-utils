from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Union

from scalecodec import ScaleBytes

from .substrate_interface import create_connection_by_url
from .metadata_interaction import get_properties

from substrateinterface import SubstrateInterface


class Chain():
    substrate: SubstrateInterface

    assets: List[ChainAsset]

    def __init__(self, arg):
        self.chainId = arg.get("chainId")
        self.parentId = arg.get("parentId")
        self.name = arg.get("name")
        self.assets = [ChainAsset(data) for data in arg.get("assets")]
        self.nodes = arg.get("nodes")
        self.explorers = arg.get("explorers")
        self.addressPrefix = arg.get("addressPrefix")
        self.externalApi = arg.get("externalApi")
        self.options = arg.get("options")
        self.substrate = None
        self.properties = None

    def create_connection(self, type_registry=None) -> SubstrateInterface:
        for node in self.nodes:
            try:
                print("Connecting to ", node.get('url'))
                self.substrate = create_connection_by_url(node.get('url'), type_registry=type_registry)
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
        return "ethereumBased" in self.options

    def get_asset(self, symbol: str) -> ChainAsset:
        return next((a for a in self.assets if a.symbol == symbol))


class ChainAsset:
    _data: dict

    symbol: str
    type: AssetType

    def __init__(self, data: dict):
        self._data = data

        self.symbol = data["symbol"]
        self.type = self._construct_type(data)

    # Backward-compatible override for code that still thinks this is a dict
    def __getitem__(self, item):
        return self._data[item]

    def unified_symbol(self) -> str:
        return self.symbol.removeprefix("xc")

    @staticmethod
    def _construct_type(data: dict) -> AssetType:
        type_label = data.get("type", "native")
        type_extras = data.get("typeExtras", {})

        match type_label:
            case "native":
                return NativeAssetType()
            case "statemine":
                return StatemineAssetType(type_extras)
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
