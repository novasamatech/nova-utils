import json

from utils.metadata_interaction import metadata_is_v14, find_in_obj, account_does_not_need_updates, deep_search_an_elemnt_by_key, write_data_to_file
from utils.network_interaction import create_connection_by_url
from substrateinterface import SubstrateInterface, Keypair


class JsonObject:
    def __init__(
        self,
        runtime_id,
        types_balance,
        types_index,
        types_phase,
        types_address,
        types_extrinsicSignature,
        types_paraId,
        types_sp_core_crypto_accountId32,
        types_pallet_identity_types_data,
        metadata_types,
    ) -> None:
        self.runtime_id = runtime_id
        self.types = {}
        json_types = {}
        json_types["Balance"] = types_balance
        json_types["Index"] = types_index
        json_types["Phase"] = types_phase
        json_types["Address"] = types_address
        json_types["ExtrinsicSignature"] = types_extrinsicSignature
        json_types["ParaId"] = types_paraId
        json_types[find_path_in_metadata(
            "Event", metadata_types)] = "GenericEvent"
        json_types[find_path_in_metadata(
            "Call", metadata_types)] = "GenericCall"
        json_types["sp_core.crypto.AccountId32"] = types_sp_core_crypto_accountId32
        json_types["pallet_identity.types.Data"] = types_pallet_identity_types_data
        self.types.update(json_types)
        self.versioning = []

    def use_v2_weight_mapping(self, runtime_dispatch_info_obj):
        self.types["RuntimeDispatchInfo"] = runtime_dispatch_info_obj


class Properties:
    def __init__(
        self, chain_id, chain_name, chain_symbol, chain_precision, chain_prefix
    ) -> None:
        self.chainId = chain_id
        self.name = chain_name
        self.symbol = chain_symbol
        self.precision = chain_precision
        self.ss58Format = chain_prefix


def get_properties(substrate: SubstrateInterface) -> Properties:
    substrate.get_constant('system', 'ss58Prefix')
    symbol = substrate.properties["tokenSymbol"]

    if isinstance(symbol, list):
        symbol = substrate.properties["tokenSymbol"][0]

    precision = substrate.properties["tokenDecimals"]
    if isinstance(precision, list):
        precision = substrate.properties["tokenDecimals"][0]

    data_prop = Properties(
        chain_name=substrate.chain,
        chain_symbol=symbol,
        chain_prefix=substrate.ss58_format,
        chain_precision=precision,

        # The genesis hash should be obtained last, because the main object "substrate" may change after the genesis was obtained
        chain_id=substrate.get_block_hash(0)
    )
    return data_prop


def get_metadata_param(substrate: SubstrateInterface) -> JsonObject:
    metadata = substrate.get_block_metadata()
    metadata_is_v14(metadata)
    account_does_not_need_updates(substrate)
    metadata_types = metadata.value[1]["V14"]["types"]["types"]
    use_additional_type_mapping = check_fee_is_structure(substrate)

    metadata_json = JsonObject(
        runtime_id=metadata.runtime_config.active_spec_version_id,
        types_balance=find_primitive("Balance", metadata_types),
        types_index=find_primitive("Index", metadata_types),
        types_phase=find_path_in_metadata("phase", metadata_types),
        types_address=find_path_in_metadata("Address", metadata_types),
        types_extrinsicSignature=find_path_in_metadata(
            "Sr25519", metadata_types),
        types_paraId="polkadot_parachain.primitives.Id",
        types_sp_core_crypto_accountId32="GenericAccountId",
        types_pallet_identity_types_data="Data",
        metadata_types=metadata_types,
    )

    if use_additional_type_mapping:
        runtime_dispatch_info = {
            "type": "struct",
            "type_mapping": [
                [
                    "weight",
                    "sp_weights.weight_v2.Weight"
                ],
                [
                    "class",
                    "frame_support.dispatch.DispatchClass"
                ],
                [
                    "partialFee",
                    "Balance"
                ]
            ]
        }
        metadata_json.use_v2_weight_mapping(runtime_dispatch_info)

    return metadata_json


def find_type_in_metadata(name, metadata_types):
    return_data = []
    for item in find_in_obj(metadata_types, name):
        return_data.append(item)
    return return_data


def find_primitive(name, metadata_types):
    data = find_type_in_metadata(name, metadata_types)
    value = metadata_types
    for path in data[0]:
        if path == 'name':
            if value[path] == name:
                type_with_primitive = metadata_types[value["type"]]
                break
        value = value[path]
    return deep_search_an_elemnt_by_key(type_with_primitive, "primitive")


def find_path_in_metadata(name, metadata_types):
    data = find_type_in_metadata(name, metadata_types)

    def check_temp_path(path, value):
        for element in path:
            if value in element:
                return True
        return False

    if name in ['Event', 'Call']:
        new_path = find_path_in_metadata('Runtime'+name, metadata_types)
        if new_path:
            return new_path

    def return_path():
        for path in data:
            value = metadata_types
            if 'type_with_primitive' in locals():
                break
            for path_element in path:
                if 'path' in value:
                    temp_path = value['path']
                if path_element == 'name':
                    if value[path_element] == name:
                        try:
                            type_with_primitive = metadata_types[value["type"]]
                        except (KeyError, TypeError):
                            # Find correct ExtrinsicSignature
                            if check_temp_path(temp_path, 'MultiSignature'):
                                return ".".join(temp_path)
                        break
                # Find correct Event and Call
                if path[-1] == path_element and check_temp_path(temp_path, '_runtime') and len(temp_path) == 2:
                    return ".".join(temp_path)

                value = value[path_element]
        found_path = deep_search_an_elemnt_by_key(type_with_primitive, "path")
        return ".".join(found_path)

    return return_path()


def check_fee_is_structure(substrate: SubstrateInterface):
    weight = substrate.get_constant('System', 'BlockWeights').value
    base_extrinsic = weight.get('per_class').get(
        'normal').get('base_extrinsic')
    if isinstance(base_extrinsic, dict):
        return True
    else:
        return False


def main():
    # user_input = input(
    #     "Enter a url for collect data, url should start with wss:\n")
    # url = user_input.strip()
    url = "wss://kusama-rpc.polkadot.io"
    print("Data collecting in process and will write to file in current directory.")

    substrate = create_connection_by_url(url)
    json_metadata = get_metadata_param(substrate)
    json_property = get_properties(substrate)
    write_data_to_file(
        json_property.name + "_types.json", json.dumps(json_metadata.__dict__, indent=2)
    )
    write_data_to_file(
        json_property.name +
        "_property.json", json.dumps(json_property.__dict__, indent=2)
    )
    print("Success! \ncheck " + json_property.name + "_* files")


if __name__ == "__main__":
    main()
