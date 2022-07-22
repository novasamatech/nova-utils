from typing import Optional
from PyInquirer import prompt
from utils.data_model.base_model import BaseParameters
from utils.data_model.xcm_json_model import XcmTransfer, Destination, Fee, FeeMode, Asset, XcmJson, Network
from utils.useful_functions import *
from utils.questions import network_questions, destination_questions, new_network_questions, asset_location_question, asset_question

chains_json_version = 'v4'
xcm_json_version = 'v2'

chains_json_path = f"./chains/{chains_json_version}/chains_dev.json"
xcm_json_path = f"./xcm/{xcm_json_version}/transfers_dev.json"

chains_json = parse_json_file(chains_json_path)
xcm_json = parse_json_file(xcm_json_path)


def network_already_added(chain_name) -> bool:

    xcm_object = XcmJson(**xcm_json)

    destination_chain = find_chain(chains_json, chain_name)

    if ([xcm_chain for xcm_chain in xcm_object.chains if xcm_chain.chainId == destination_chain.chainId]):
        return True
    else:
        return False


def should_create_new_destination(
    base_parameters: BaseParameters,
) -> bool:

    xcm_object = XcmJson(**xcm_json)

    source_chain = find_chain(chains_json, base_parameters.source_network)
    destination_chain = find_chain(
        chains_json, base_parameters.destination_network)

    source_xcm_network = [xcm for xcm in xcm_object.chains if xcm.chainId ==
                          source_chain.chainId]

    if (source_xcm_network):
        added_xcm_asset = [
            asset for asset in source_xcm_network[0].assets if asset.assetLocation == base_parameters.asset]
        if (added_xcm_asset):

            for xcm_transfer_destination in added_xcm_asset[0].xcmTransfers:
                if (xcm_transfer_destination.destination.chainId == destination_chain.chainId):
                    return False

    return True


def token_already_added(
    base_parameters: BaseParameters,
) -> bool:

    xcm_object = XcmJson(**xcm_json)
    source_chain = find_chain(chains_json, base_parameters.source_network)

    xcm_chain = [chain for chain in xcm_object.chains if chain.chainId ==
                 source_chain.chainId][0]

    for asset in xcm_chain.assets:
        if (asset.assetLocation == base_parameters.asset):
            return True

    return False


def such_destination_was_already_added(
    base_parameters: BaseParameters,
) -> XcmTransfer:

    xcm_object = XcmJson(**xcm_json)
    destination_chain = find_chain(
        chains_json, base_parameters.destination_network)

    for chain in xcm_object.chains:
        for asset in chain.assets:
            if (asset.assetLocation == base_parameters.asset):
                for destination in asset.xcmTransfers:
                    if (destination.destination.chainId == destination_chain.chainId):
                        return destination


def such_destination_was_already_added(base_parameters: BaseParameters) -> XcmTransfer:
    xcm_object = XcmJson(**xcm_json)

    destination_chain = find_chain(
        chains_json, base_parameters.destination_network)

    for chain in xcm_object.chains:
        for asset in chain.assets:
            if (asset.assetLocation == base_parameters.asset):
                for destination in asset.xcmTransfers:
                    if (destination.destination.chainId == destination_chain.chainId):
                        return destination


def build_xcm_transfer(
    base_parameters: BaseParameters,
    already_added_destination: XcmTransfer
) -> XcmTransfer:
    if (should_create_new_destination(base_parameters)):
        xcm_object = XcmJson(**xcm_json)

        chain = find_chain(chains_json, base_parameters.destination_network)

        asset = find_asset_in_chain(chain, base_parameters.asset)
        destination_params = prompt(destination_questions(xcm_json))

        if (already_added_destination):
            fee_mode = FeeMode(
                type=destination_params.get('fee_type'),
                value=already_added_destination.destination.fee.mode.value
            )
        else:
            fee_mode = FeeMode(
                type=destination_params.get('fee_type')
            )

        fee = Fee(
            mode=fee_mode,
            instructions=destination_params.get('instructions')
        )

        if (already_added_destination is None and destination_params.get('fee_type') != 'standard'):
            fee.calculate_fee(
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


def create_new_asset(
    base_parameters: BaseParameters,
    asset,
    assetLocationPath,
    already_added_destination: Optional[XcmTransfer] = None
) -> Asset:

    destination = build_xcm_transfer(
        base_parameters, already_added_destination)

    new_asset = Asset(
        assetId=asset.assetId,
        assetLocation=base_parameters.asset,
        assetLocationPath=assetLocationPath,
        xcmTransfers=[destination]
    )

    return new_asset


def create_new_network(
    base_parameters: BaseParameters,
    already_added_destination: Optional[XcmTransfer] = None
) -> XcmJson:
    xcm_object = XcmJson(**xcm_json)

    network_param = prompt(new_network_questions())

    searched_chain = find_chain(chains_json, base_parameters.source_network)
    asset = find_asset_in_chain(searched_chain, base_parameters.asset)

    new_asset = create_new_asset(
        base_parameters,
        asset,
        network_param.get('assetLocationPath'),
        already_added_destination
    )

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


def update_destinations(
    base_parameters: BaseParameters,
    already_added_destination: Optional[XcmTransfer] = None
) -> XcmJson:

    if (token_already_added(base_parameters)):
        destination = build_xcm_transfer(
            base_parameters, already_added_destination)
        return push_new_destination(base_parameters, destination)
    else:
        xcm_object = XcmJson(**xcm_json)

        asset_location = prompt(asset_location_question())

        searched_chain = find_chain(
            chains_json, base_parameters.source_network)

        asset = find_asset_in_chain(searched_chain, base_parameters.asset)

        new_asset = create_new_asset(
            base_parameters=base_parameters,
            asset=asset,
            assetLocationPath=asset_location.get('assetLocationPath'),
            destination=destination
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
    # TODO add case with adding new token to the xcm list

    network_answers = prompt(network_questions(
        adding_asset.get('asset'), chains_json))
    # Merge asset with network data to create base_parameter object
    network_answers['asset'] = adding_asset.get('asset')

    base_parameters = BaseParameters(**network_answers)

    already_added_destination = such_destination_was_already_added(
        base_parameters)

    if (network_already_added(base_parameters.source_network)):
        updated_xcm_json = update_destinations(
            base_parameters, already_added_destination)
    else:
        updated_xcm_json = create_new_network(
            base_parameters, already_added_destination)

    return write_new_file(updated_xcm_json.toJSON(), xcm_json_path)


if __name__ == "__main__":
    main()
