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
        event_type = find_certain_type_in_metadata("Event", metadata_types)
        call_type = find_certain_type_in_metadata("Call", metadata_types)
        json_types[return_type_path(event_type, 'path')] = "GenericEvent"
        json_types[return_type_path(call_type, 'path')] = "GenericCall"
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
        types_phase=find_path_for_type_in_metadata("Phase", metadata_types),
        types_address=find_path_for_type_in_metadata(
            "AccountIdLookupOf<T>", metadata_types),
        types_extrinsicSignature=find_path_for_type_in_metadata(
            "Signature", metadata_types),
        types_paraId="polkadot_parachain.primitives.Id",
        types_sp_core_crypto_accountId32="GenericAccountId",
        types_pallet_identity_types_data="Data",
        metadata_types=metadata_types,
    )

    if use_additional_type_mapping:
        runtime_dispatch_info = find_dispatch_info(
            'DispatchInfo', metadata_types)
        metadata_json.use_v2_weight_mapping(runtime_dispatch_info)

    return metadata_json


def find_type_id_in_metadata(name, metadata_types, default_path_marker='typeName'):
    data_set = find_type_in_metadata(name, metadata_types)
    for data in data_set:
        value = metadata_types
        for path in data:
            if path == default_path_marker:
                return value['type']
            value = value[path]

    # if nothing were found, then try to find with another marker
    type_found_by_name = find_type_id_in_metadata(name, metadata_types, default_path_marker='name')
    if type_found_by_name:
        return type_found_by_name
    else:
        raise Exception(f"Can't find type_id for {name}")


def find_dispatch_info(name, metadata_types):
    dispatch_info = find_certain_type_in_metadata(name, metadata_types)
    weight, dispatch_class, _ = dispatch_info['type']['def']['composite']['fields']
    dispatch_class_path = return_type_path(
        metadata_types[dispatch_class['type']], 'path')
    weight_path = return_type_path(
        metadata_types[weight['type']], 'path')
    dispatch_info_object = {"type": "struct", "type_mapping": [["weight", weight_path], [
        "class", dispatch_class_path], ["partialFee", "Balance"]]}
    return dispatch_info_object


def find_primitive(name, metadata_types):
    type_id = find_type_id_in_metadata(name, metadata_types)
    type_with_primitive = metadata_types[type_id]
    return deep_search_an_elemnt_by_key(type_with_primitive, "primitive")


def find_path_for_type_in_metadata(name, metadata_types):
    type_id = find_type_id_in_metadata(name, metadata_types)
    return return_type_path(metadata_types[type_id], "path")


def find_certain_type_in_metadata(name, metadata_types):
    if name in ['Event', 'Call']:
        new_path = find_certain_type_in_metadata(
            'Runtime'+name, metadata_types)
        if new_path:
            return new_path

    data_set = find_type_in_metadata(name, metadata_types)
    if len(data_set) == 1:
        type_id = data_set[0][0]
        return metadata_types[type_id]

    for data in data_set:
        value = metadata_types
        for path in data:
            if path == 'path':
                return metadata_types[data[0]]
            value = value[path]

    raise Exception(f"Can't find any type in metadata for: {name}")


def check_fee_is_structure(substrate: SubstrateInterface):
    weight = substrate.get_constant('System', 'BlockWeights').value
    base_extrinsic = weight.get('per_class').get(
        'normal').get('base_extrinsic')
    if isinstance(base_extrinsic, dict):
        return True
    else:
        return False


def return_type_path(metadata_type, search_key):
    found_path = deep_search_an_elemnt_by_key(metadata_type, search_key)
    return ".".join(found_path)


def find_type_in_metadata(name, metadata_types):
    return_data = []
    for item in find_in_obj(metadata_types, name):
        return_data.append(item)
    return return_data


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
        json_property.name +
        "_types.json", json.dumps(json_metadata.__dict__, indent=2)
    )
    write_data_to_file(
        json_property.name +
        "_property.json", json.dumps(json_property.__dict__, indent=2)
    )
    print("Success! \ncheck " + json_property.name + "_* files")


if __name__ == "__main__":
    main()
