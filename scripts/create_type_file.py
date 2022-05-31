import json
from typing import List
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
        network_runtime_name = get_current_path_from_metadata(
            "Event", metadata_types
        ).split(".")[0]
        json_types[network_runtime_name + ".Event"] = "GenericEvent"
        json_types[network_runtime_name + ".Call"] = "GenericCall"
        json_types["sp_core.crypto.AccountId32"] = types_sp_core_crypto_accountId32
        json_types["pallet_identity.types.Data"] = types_pallet_identity_types_data
        self.types.update(json_types)
        self.versioning = []


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

    if (isinstance(symbol, list)):
        symbol = substrate.properties["tokenSymbol"][0]

    precision = substrate.properties["tokenDecimals"]
    if (isinstance(precision, list)):
        precision = substrate.properties["tokenDecimals"][0]

    data_prop = Properties(
        chain_name=substrate.chain,
        chain_symbol=symbol,
        chain_prefix= substrate.ss58_format,
        chain_precision=precision,

        # The genesis hash should be obtained last, because the main object "substrate" may change after the genesis was obtained
        chain_id=substrate.get_block_hash(0)
    )
    return data_prop


def get_metadata_param(substrate: SubstrateInterface) -> JsonObject:
    metadata = substrate.get_block_metadata()
    metadata_is_v14(metadata)
    account_do_not_need_updates(substrate)
    metadata_types = metadata.value[1]["V14"]["types"]["types"]

    metadata_json = JsonObject(
        runtime_id=metadata.runtime_config.active_spec_version_id,
        types_balance=get_primitive_from_metadata("Balance", metadata_types),
        types_index=get_primitive_for_index("AccountInfo", metadata_types),
        types_phase=get_path_from_metadata("Phase", metadata_types),
        types_address=get_path_from_metadata("Address", metadata_types),
        types_extrinsicSignature=get_crypto_path_from_metadata(
            "Sr25519", metadata_types
        ),
        types_paraId="polkadot_parachain.primitives.Id",
        types_sp_core_crypto_accountId32="GenericAccountId",
        types_pallet_identity_types_data="Data",
        metadata_types=metadata_types,
    )
    return metadata_json


def metadata_is_v14(metadata):
    if "V14" in metadata.value[1].keys():
        return True
    else:
        raise Exception("It's not a v14 runtime: %s" % (metadata.value[1].keys()))


def account_do_not_need_updates(substrate: SubstrateInterface):
    keypair = Keypair.create_from_uri("//Alice")
    account_info = substrate.query("System", "Account", params=[keypair.ss58_address])
    elements = ["nonce", "free", "reserved", "misc_frozen", "fee_frozen"]
    if len(account_info.value["data"]) != 4:
        raise Exception("Account info is changed: %s" % (account_info))
    for element in elements:
        if element in account_info:
            continue
        elif element in account_info["data"]:
            continue
        else:
            raise Exception("Account info is changed: %s" % (account_info))


def find_type_in_metadata(name, metadata_types):
    return_data = []
    for item in find_in_obj(metadata_types, name):
        return_data.append(item)
    return return_data


def get_primitive_for_index(name, metadata_types):
    data = find_type_in_metadata(name, metadata_types)
    value = metadata_types
    for path in data[0]:
        if path == "path":
            new_path = find_type_in_metadata("Index", value)
            for key in new_path[0]:
                if key == "name":
                    continue
                value = value[key]
            break
        value = value[path]
    type_with_primitive = metadata_types[value["type"]]
    return type_with_primitive["type"]["def"]["primitive"]


def get_primitive_from_metadata(name, metadata_types):
    data = find_type_in_metadata(name, metadata_types)
    value = metadata_types
    for path in data[0]:
        if path == "name":
            continue
        value = value[path]
    type_with_primitive = metadata_types[value["type"]]
    return type_with_primitive["type"]["def"]["primitive"]


def get_path_from_metadata(name, metadata_types):
    data = find_type_in_metadata(name, metadata_types)
    value = metadata_types
    for path in data[0]:
        if path in ("typeName", "name"):
            continue
        value = value[path]
    type_with_primitive = metadata_types[value["type"]]
    returned_path = ".".join(str(x) for x in type_with_primitive["type"]["path"])
    return returned_path


def get_current_path_from_metadata(name, metadata_types):
    data = find_type_in_metadata(name, metadata_types)
    value = metadata_types
    for path in data[0]:
        if path == "path":
            value = value[path]
            returned_path = ".".join(str(x) for x in value)
            return returned_path
        value = value[path]
    return "Can't find value"


def get_crypto_path_from_metadata(name, metadata_types):
    data = find_type_in_metadata(name, metadata_types)
    value = metadata_types
    for variants in data:
        wrong_path = False
        for path in variants:
            if path == "def":
                for list_val in value["path"]:
                    if list_val == "did":
                        wrong_path = True
                        break
                if wrong_path:
                    break
                value = value["path"]
                returned_path = ".".join(str(x) for x in value)
                return returned_path
            value = value[path]
        value = metadata_types
    return "Can't find value"


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


def create_connection_by_url(url):
    try:
        substrate = SubstrateInterface(url=url, use_remote_preset=True)
    except ConnectionRefusedError and TimeoutError:
        print("⚠️ Can't connect by %s, check it is available?" % (url))
        raise

    return substrate


def write_data_to_file(name, data: str):

    with open(name, "w") as file:
        file.write(data)


def main():

    user_input = input("Enter a url for collect data, url should start with wss:\n")
    url = user_input.strip()

    print("Data collecting in process and will write to file in current directory.")

    substrate = create_connection_by_url(url)

    json_metadata = get_metadata_param(substrate)
    json_property = get_properties(substrate)

    write_data_to_file(
        json_property.name + "_types.json", json.dumps(json_metadata.__dict__)
    )
    write_data_to_file(
        json_property.name + "_property.json", json.dumps(json_property.__dict__)
    )

    print("Success! \ncheck " + json_property.name + "_* files")


if __name__ == "__main__":
    main()
