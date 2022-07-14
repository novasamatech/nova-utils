from .base_model import BaseObject
from typing import List


class ChainAsset(BaseObject):
    assetId: int
    symbol: str
    precision: int
    priceId: str
    type: str
    icon: str
    typeExtras: object
    staking: str
    buyProviders: object

    def __init__(self, **kwargs):
        for k in kwargs.keys():
            self.__setattr__(k, kwargs[k])


class Chain(BaseObject):
    parentId: str
    chainId: str
    name: str
    assets: List[ChainAsset]
    nodes: List[object]
    explorers: List[object]
    color: str
    icon: str
    addressPrefix: int
    types: object
    externalApi: object
    options: List[object]

    def __init__(self, **kwargs):
        for k in kwargs.keys():
            if (k == 'assets'):
                self.assets = []
                for asset in kwargs[k]:
                    self.assets.append(ChainAsset(**asset))
                continue
            self.__setattr__(k, kwargs[k])