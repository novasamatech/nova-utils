from PyInquirer import prompt
from generate_xcm_table import build_data_from_jsons
from utils.model.base_model import BaseParameters
from utils.model.xcm_json_model import XcmTransfer, Destination, Fee, Asset, XcmJson, Network
from utils.useful_functions import *
from utils.questions import build_initial_questions, destination_questions, new_network_questions, update_network_questions


chains_json = parse_json_file('./chains/v4/chains_dev.json')
xcm_json = parse_json_file('./xcm/v2/transfers_dev.json')
xcm_list = build_data_from_jsons()


def network_already_added(network):
    if([xcm for xcm in xcm_list if xcm.chainName == network]):
        return True
    return False


def should_create_new_destination(base_parameters: BaseParameters):
    xcm_network = [xcm for xcm in xcm_list if xcm.chainName ==
                   base_parameters.source_network]
    if (xcm_network):
        xcm_asset = [asset for asset in xcm_network[0].assets if asset.get(
            'asset') == base_parameters.asset]
        if (xcm_asset):
            if (base_parameters.destination_network in xcm_asset[0].get('destination')):
                return False
    return True


def token_already_added(base_parameters):
    network = [chain for chain in xcm_list if chain.chainName ==
               base_parameters.source_network][0]
    token = find_element_in_array_by_condition(
        network.assets,
        'asset',
        base_parameters.asset
    )
    if (token):
        return True
    return False


def build_xcm_transfer(base_parameters: BaseParameters) -> XcmTransfer:
    if (should_create_new_destination(base_parameters)):
        xcm_object = XcmJson(**xcm_json)

        chain = find_chain(chains_json, base_parameters.destination_network)

        asset = find_asset_in_chain(chain, base_parameters.asset)
        destination_params = prompt(destination_questions())
        # destination_params = {'destination_type': 'xtokens', 'instructions': 'xtokensDest', 'fee_type': 'proportional'}

        fee = Fee(
            fee_type=destination_params.get('fee_type'),
            instructions=destination_params.get('instructions'),
            network=chain,
            xcm_asset=find_assetsLocation(
                base_parameters, xcm_object=xcm_object)
        )

        destination = Destination(
            chainId=chain.chainId,
            assetId=asset.assetId,
            fee=fee
        )

        xcm_transfer = XcmTransfer(
            destination=destination,
            type=destination_params.get('destination_type')
        )

        return xcm_transfer
    else:
        raise Exception('Selected asset already added for that direction')


def create_new_asset(base_parameters: BaseParameters, asset, assetLocationPath) -> Asset:

    xcm_transfer = build_xcm_transfer(base_parameters)

    new_asset = Asset(
        assetId=asset.assetId,
        assetLocation=base_parameters.asset,
        assetLocationPath=assetLocationPath,
        xcmTransfers=[xcm_transfer]
    )

    return new_asset


def create_new_network(base_parameters: BaseParameters) -> XcmJson:
    xcm_object = XcmJson(**xcm_json)

    network_param = prompt(new_network_questions())
    # network_param = {'networkBaseWeight': 150000000, 'assetLocationPath': 'absolute'}
    searched_chain = find_chain(chains_json, base_parameters.source_network)

    asset = find_asset_in_chain(searched_chain, base_parameters.asset)

    new_asset = create_new_asset(
        base_parameters, asset, network_param.get('assetLocationPath'))

    network = Network(searched_chain.chainId, new_asset)

    xcm_object.chains.append(network)

    xcm_object.networkBaseWeight[network.chainId] = str(
        network_param.get('networkBaseWeight'))

    return xcm_object


def push_new_destination(base_parameters: BaseParameters, xcm_transfer: XcmTransfer):

    xcm_object = XcmJson(**xcm_json)

    searched_chain = find_chain(chains_json, base_parameters.source_network)

    for chain in xcm_object.chains:
        if (chain.chainId == searched_chain.chainId):
            for asset in chain.assets:
                if (asset.assetLocation == base_parameters.asset):
                    asset.xcmTransfers.append(xcm_transfer.__dict__)

    return xcm_object


def update_destinations(base_parameters: BaseParameters):

    if (token_already_added(base_parameters)):
        xcm_transfer = build_xcm_transfer(base_parameters)
        return push_new_destination(base_parameters, xcm_transfer)
    else:
        xcm_object = XcmJson(**xcm_json)

        token_param = prompt(update_network_questions())

        searched_chain = find_chain(
            chains_json, base_parameters.source_network)

        asset = find_asset_in_chain(searched_chain, base_parameters.asset)

        new_asset = create_new_asset(
            base_parameters=base_parameters,
            asset=asset,
            assetLocationPath=token_param.get('assetLocationPath')
        )

        for chain in xcm_object.chains:
            if (chain.chainId == searched_chain.chainId):
                chain.assets.append(new_asset)

        return xcm_object


def main():
    first_input = prompt(build_initial_questions())
    # first_input = {'asset': 'HKO', 'source_network': 'Parallel Heiko', 'destination_network': 'Moonriver'}
    base_parameters = BaseParameters(**first_input)

    if (network_already_added(base_parameters.source_network)):
        updated_xcm_json = update_destinations(base_parameters)
    else:
        updated_xcm_json = create_new_network(base_parameters)

    write_new_file(updated_xcm_json.toJSON(),
                   "./xcm/v2/transfers_dev_new.json")


if __name__ == "__main__":
    main()
