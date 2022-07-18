
from .data_model.chain_json_model import Chain
from .useful_functions import deep_search_in_object, find_asset_in_chain


def asset_question(xcm_json):
    assets = []
    for asset in xcm_json.get('assetsLocation'):
        assets.append(asset)
    question = {
        'type': 'list',
        'name': 'asset',
        'message': 'Please select the asset you want to add:',
        'choices': assets
    }
    return question


def network_questions(asset, chains_json):
    chains = []
    for chain in chains_json:
        chain_object = Chain(**chain)
        if (find_asset_in_chain(chain_object, asset)):
            chains.append(chain_object.name)
    chains.sort()
    questions = [
        {
            'type': 'list',
            'name': 'source_network',
            'message': 'Please select the SOURCE network:',
            'choices': chains
        },

        {
            'type': 'list',
            'name': 'destination_network',
            'message': 'Please select the DESTINATION network:',
            'choices': chains
        }]
    return questions


def destination_questions(xcm_json):
    instructions = []
    for instruction in xcm_json.get('instructions'):
        instructions.append(instruction)
    questions = [
        {
            'type': 'list',
            'name': 'destination_type',
            'message': 'Please select the XCM type',
            'choices': ['xcmpallet', 'xtokens', 'xcmpallet-teleport']
        },
        {
            'type': 'list',
            'name': 'instructions',
            'message': 'Please select the Instruction for destination fee',
            'choices': instructions
        },
        {
            'type': 'list',
            'name': 'fee_type',
            'message': 'Please select the Fee type for that destination',
            'choices': ['standard', 'proportional']
        }
    ]
    return questions


def new_network_questions():
    questions = [
        {
            'type': 'input',
            'name': 'networkBaseWeight',
            'message': 'Enter network Base Weight:',
            'filter': lambda val: int(val),
        },
        {
            'type': 'list',
            'name': 'assetLocationPath',
            'message': 'Choose location path for the asset:',
            'choices': ['relative', 'absolute', 'concrete']
        }
    ]
    return questions


def asset_location_question():
    question = {
        'type': 'list',
        'name': 'assetLocationPath',
        'message': 'Choose location path for the asset:',
        'choices': ['relative', 'absolute', 'concrete']
    }
    return question


def coefficient_question():
    question = {
        'type': 'input',
        'name': 'coefficient',
        'message': 'Enter float number which will multiplier on base network fee',
        'filter': lambda val: float(val),
    }

    return question
