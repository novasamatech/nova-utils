from PyInquirer import prompt
from generate_xcm_table import build_data_from_jsons
from utils.data_model.base_model import BaseParameters
from utils.data_model.xcm_json_model import XcmTransfer, Destination, Fee, Asset, XcmJson, Network
from utils.useful_functions import *
from utils.questions import network_questions, destination_questions, new_network_questions, asset_location_question, asset_question

chains_json_path = './chains/v4/chains_dev.json'
xcm_json_path = './xcm/v2/transfers_dev.json'
new_xcm_json_path = "./xcm/v2/transfers_dev_new.json"

chains_json = parse_json_file(chains_json_path)
xcm_json = parse_json_file(xcm_json_path)
xcm_list = build_data_from_jsons()


def network_already_added(network) -> bool:
    if([xcm for xcm in xcm_list if xcm.chainName == network]):
        return True
    return False


def should_create_new_destination(base_parameters: BaseParameters) -> bool:
    xcm_network = [xcm for xcm in xcm_list if xcm.chainName ==
                   base_parameters.source_network]
    if (xcm_network):
        xcm_asset = [asset for asset in xcm_network[0].assets if asset.get(
            'asset') == base_parameters.asset]
        if (xcm_asset):
            if (base_parameters.destination_network in xcm_asset[0].get('destination')):
                return False
    return True


def token_already_added(base_parameters) -> bool:
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
        destination_params = prompt(destination_questions(xcm_json))

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

    searched_chain = find_chain(chains_json, base_parameters.source_network)
    asset = find_asset_in_chain(searched_chain, base_parameters.asset)

    new_asset = create_new_asset(
        base_parameters, asset, network_param.get('assetLocationPath'))

    network = Network(searched_chain.chainId, new_asset)

    xcm_object.chains.append(network)

    xcm_object.networkBaseWeight[network.chainId] = str(
        network_param.get('networkBaseWeight'))

    return xcm_object


def push_new_destination(base_parameters: BaseParameters, xcm_transfer: XcmTransfer) -> XcmJson:

    xcm_object = XcmJson(**xcm_json)

    searched_chain = find_chain(chains_json, base_parameters.source_network)

    for chain in xcm_object.chains:
        if (chain.chainId == searched_chain.chainId):
            for asset in chain.assets:
                if (asset.assetLocation == base_parameters.asset):
                    asset.xcmTransfers.append(xcm_transfer.__dict__)

    return xcm_object


def update_destinations(base_parameters: BaseParameters) -> XcmJson:

    if (token_already_added(base_parameters)):
        xcm_transfer = build_xcm_transfer(base_parameters)
        return push_new_destination(base_parameters, xcm_transfer)
    else:
        xcm_object = XcmJson(**xcm_json)

        asset_location = prompt(asset_location_question())

        searched_chain = find_chain(
            chains_json, base_parameters.source_network)

        asset = find_asset_in_chain(searched_chain, base_parameters.asset)

        new_asset = create_new_asset(
            base_parameters=base_parameters,
            asset=asset,
            assetLocationPath=asset_location.get('assetLocationPath')
        )

        for chain in xcm_object.chains:
            if (chain.chainId == searched_chain.chainId):
                chain.assets.append(new_asset)

        return xcm_object


def main():
    '''
    That script uses for update data in xcm/../transfers.json file.

    To begin you must choose:
    1. The asset which you want to add
        - if that asset haven't added yet in the json file, you should add it manually in assetsLocation part.
    2. Source network
    3. Destination network

    Next, input data will compare with actual json's data and selected one of the scenario:
    - Create new network
    - Add new asset to existing network
    - Update destinations array for existing network and asset

    For each scenario may be asked addition questions, all question list may be found in utils/questions.py

    In the end will be calculated base_fee for destination network by functions from utils/fee_calculation_functions.py and for getting final fee you should add the coefficient which will multiplier:
    (base_fee * coefficient) = final_fee
    '''
    adding_asset = prompt(asset_question(xcm_json))

    network_answers = prompt(network_questions(adding_asset.get('asset'), chains_json))
    network_answers['asset'] = adding_asset.get('asset') # Merge asset with network data to create base_parameter object

    base_parameters = BaseParameters(**network_answers)

    if (network_already_added(base_parameters.source_network)):
        updated_xcm_json = update_destinations(base_parameters)
    else:
        updated_xcm_json = create_new_network(base_parameters)

    write_new_file(updated_xcm_json.toJSON(), new_xcm_json_path)


if __name__ == "__main__":
    main()
