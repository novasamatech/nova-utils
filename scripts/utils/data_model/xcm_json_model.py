import math
from typing import List

from .base_model import BaseObject
from .chain_json_model import Chain
from PyInquirer import prompt
from utils.fee_calculation_functions import biforst_base_fee, heiko_base_fee, kintsugi_base_fee, karura_base_fee, turing_base_fee, moonriver_fee_calculation

from utils.questions import coefficient_question



class Fee(BaseObject):
    mode: dict
    instructions: str

    def __init__(self, fee_type, instructions, network: Chain, xcm_asset):

        if (fee_type == 'standard'):
            self.mode = {
                "type": fee_type
            }
        elif (fee_type == 'proportional'):
            self.mode = {
                "type": fee_type,
                "value": str(self.calculate_fee(network, xcm_asset))
            }
        else:
            raise Exception('Wrong fee type')

        self.instructions = instructions

    def calculate_fee(self, network: Chain, xcm_asset):

        def base_fee_and_multiplier(base_fee):
            coefficient_input = prompt(coefficient_question())
            coefficient = coefficient_input.get('coefficient')

            return math.ceil(base_fee * coefficient)

        if (network.name == "Bifrost"):
            base_fee = biforst_base_fee(network)
        elif (network.name == "Parallel Heiko"):
            base_fee = heiko_base_fee(network)
        elif (network.name == "Moonriver"):
            base_fee = moonriver_fee_calculation(network, xcm_asset)
        elif (network.name == "Kintsugi"):
            base_fee = kintsugi_base_fee(network)
        elif (network.name == "Karura"):
            base_fee = karura_base_fee(network)
        elif (network.name == "Turing"):
            base_fee = turing_base_fee(network)
        else:
            raise Exception(
                'Fee function is not available for network %s' % network.name)

        return base_fee_and_multiplier(base_fee)


class Destination(BaseObject):

    chainId: str
    assetId: int
    fee: Fee

    def __init__(self, chainId, assetId, fee: Fee):
        self.chainId = chainId
        self.assetId = assetId
        self.fee = fee.__dict__


class XcmTransfer(BaseObject):

    destination: Destination
    type: str

    def __init__(self, destination: Destination, type):
        self.destination = destination.__dict__
        self.type = type


class Asset(BaseObject):

    assetId: int
    assetLocation: str
    assetLocationPath: dict
    xcmTransfers: List[XcmTransfer]

    def __init__(self, assetId, assetLocation, assetLocationPath, xcmTransfers):
        self.assetId = assetId
        self.assetLocation = assetLocation
        if (isinstance(assetLocationPath, dict)):
            self.assetLocationPath = assetLocationPath
        else:
            self.assetLocationPath = {'type': assetLocationPath}
        self.xcmTransfers = []
        for transfer in xcmTransfers:
            self.xcmTransfers.append(transfer)


class Network(BaseObject):

    chainId: str
    assets: List[Asset]

    def __init__(self, chainId, assets: Asset):
        self.chainId = chainId
        if (isinstance(assets, list)):
            self.assets = []
            for asset in assets:
                self.assets.append(Asset(**asset))
        else:
            self.assets = [assets]


class XcmJson(BaseObject):
    assetsLocation: object
    instructions: object
    networkBaseWeight: object
    chains: List[Network]

    def __init__(self, **kwargs):
        for k in kwargs.keys():
            if (k == 'chains'):
                self.chains = []
                for chain in kwargs[k]:
                    self.chains.append(Network(**chain))
                continue
            self.__setattr__(k, kwargs[k])