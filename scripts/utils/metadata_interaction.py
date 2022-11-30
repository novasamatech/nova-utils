from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException


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
    try:
        metadata = substrate.get_block_metadata()
    except Exception as error:
        print(f"There is some error with getting metadata from remote, Error:\n{error}")
        return None
    metadata_is_v14(metadata)
    account_does_not_need_updates(substrate)
    metadata_types = metadata.value[1]["V14"]["types"]["types"]
    can_calculate_fee = check_fee_is_calculating(substrate)
    address_type = find_certain_type_in_metadata("MultiAddress", metadata_types)
    if address_type is None: # Some network use AccountId32 as base
        address_type = find_certain_type_in_metadata("AccountId32", metadata_types)
    signature_type_path = find_path_for_type_in_metadata("Signature", metadata_types, check_path='MultiSignature')
    if signature_type_path is None:
        signature_type = find_certain_type_in_metadata("MultiSignature", metadata_types)
        signature_type_path = return_type_path(signature_type, 'path')

    metadata_json = JsonObject(
        runtime_id=metadata.runtime_config.active_spec_version_id,
        types_balance=find_primitive("Balance", metadata_types),
        types_index=find_primitive("Index", metadata_types),
        types_phase=find_path_for_type_in_metadata("Phase", metadata_types),
        types_address=return_type_path(address_type, 'path'),
        types_extrinsicSignature=signature_type_path,
        types_paraId="polkadot_parachain.primitives.Id",
        types_sp_core_crypto_accountId32="GenericAccountId",
        types_pallet_identity_types_data="Data",
        metadata_types=metadata_types,
    )

    if can_calculate_fee is False:
        runtime_dispatch_info = find_dispatch_info(
            'DispatchInfo', metadata_types)
        metadata_json.use_v2_weight_mapping(runtime_dispatch_info)

    return metadata_json


def find_type_id_in_metadata(name, metadata_types, default_path_marker='typeName', check_path=None):
    data_set = find_type_in_metadata(name, metadata_types)
    for data in data_set:
        value = metadata_types
        for path in data:
            if path == default_path_marker:
                if check_path is not None:
                    if check_runtime_path(metadata_types[value['type']], check_path):
                        return value['type']
                    else:
                        value = value[path]
                        continue
                return value['type']
            value = value[path]

    # if nothing were found, then try to find with another marker
    if default_path_marker != 'name':
        return find_type_id_in_metadata(name, metadata_types, default_path_marker='name', check_path=check_path)
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


def find_path_for_type_in_metadata(name, metadata_types, check_path=None):
    type_id = find_type_id_in_metadata(name, metadata_types, check_path=check_path)
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
                if any(call in name for call in ('Event', 'Call')):
                    if check_runtime_path(metadata_types[data[0]], 'runtime'):
                        return metadata_types[data[0]]
                    else:
                        value = value[path]
                        continue
                else:
                    return metadata_types[data[0]]
            value = value[path]


def check_runtime_path(runtime_type, part_of_path):
    runtime_path = runtime_type['type']['path']
    if bool(part_of_path in ".".join(runtime_path)):
        if len(runtime_path) <= 3:
            return True
    return False


def check_fee_is_calculating(substrate: SubstrateInterface):
    test_keypair = Keypair.create_from_uri('//Alice')
    try:
        call = substrate.compose_call(
            call_module='Balances',
            call_function='transfer',
            call_params={
                'dest': test_keypair.ss58_address,
                'value': 0,
            }
        )
        query_info = substrate.get_payment_info(call=call, keypair=test_keypair)
        return True
    except ValueError as value_error:
        print(f"Case when Balance pallet not found:\n{value_error}")
        return True
    except SubstrateRequestException as substrate_error:
        print(f"Can't calculate fee, error is: \n{substrate_error}")
        if "failed to decode" in substrate_error.args[0]['data'].lower():
            return False
        else:
            return True
    except Exception as err:
        print(f"Can't calculate fee by another reason error is: \n{err}")
        return True


def return_type_path(metadata_type, search_key):
    found_path = deep_search_an_elemnt_by_key(metadata_type, search_key)
    return ".".join(found_path)


def find_type_in_metadata(name, metadata_types):
    return_data = []
    for item in find_in_obj(metadata_types, name):
        return_data.append(item)
    return return_data


def metadata_is_v14(metadata):
    if "V14" in metadata.value[1].keys():
        return True
    else:
        raise Exception("It's not a v14 runtime: %s" % (metadata.value[1].keys()))


def account_does_not_need_updates(substrate: SubstrateInterface):
    keypair = Keypair.create_from_uri("//Alice")
    try:
        account_info = substrate.query("System", "Account", params=[keypair.ss58_address])
    # except ValueError as value_error:
    #     print(f"Error while getting an account info:\n{value_error}")
    #     account_info = substrate.query("System", "Account", params=['0xC4d9Aa77d94c36D737c5A25F5CdD0FCC7BAEf963'])
    except Exception as error:
        raise Exception(f"Can't get account info for {substrate.chain}, Error:\n{error}")

    elements = ["nonce", "free", "reserved", "misc_frozen", "fee_frozen"]
    if len(account_info.value["data"]) != 4:
        print("❌ Account info is changed: %s ❌ " % (account_info))
    for element in elements:
        if element in account_info:
            continue
        elif element in account_info["data"]:
            continue
        else:
            print("❌ Account info is changed: %s ❌ " % (account_info))


def deep_search_an_elemnt_by_key(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = deep_search_an_elemnt_by_key(v, key)
            if item is not None:
                return item
        if isinstance(v, tuple):
            for element in v:
                if isinstance(element, dict):
                    tuple_item = deep_search_an_elemnt_by_key(element, key)
                    if tuple_item is not None:
                        return tuple_item


def find_in_obj(obj, condition, path=None):

    if path is None:
        path = []

    # In case this is a list
    if isinstance(obj, list):
        for index, value in enumerate(obj):
            new_path = list(path)
            new_path.append(index)
            for result in find_in_obj(value, condition, path=new_path):
                yield result

    # In case this is a dictionary
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = list(path)
            new_path.append(key)
            for result in find_in_obj(value, condition, path=new_path):
                yield result

            if condition == key:
                new_path = list(path)
                new_path.append(key)
                yield new_path

    if condition == obj:
        new_path = list(path)
        yield new_path


def write_data_to_file(name, data: str):

    with open(name, "w") as file:
        file.write(data)
