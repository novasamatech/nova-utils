import json
from typing import List
from substrateinterface import SubstrateInterface, Keypair

url = "wss://quartz.unique.network"


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
        metadata,
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
        network_runtime_name = get_current_path_from_metadata("Event", metadata).split(
            "."
        )[0]
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
    data_prop = Properties(
        chain_id=substrate.get_block(block_number=0)["header"]["hash"],
        chain_name=substrate.chain,
        chain_symbol=substrate.properties["tokenSymbol"],
        chain_prefix=substrate.properties["ss58Format"],
        chain_precision=substrate.properties["tokenDecimals"],
    )
    return data_prop


def get_metada_param(substrate: SubstrateInterface) -> JsonObject:
    metadata = substrate.get_block_metadata()
    metadata_is_v14(metadata)
    account_do_not_need_updates(substrate)

    metadata_json = JsonObject(
        runtime_id=metadata.runtime_config.active_spec_version_id,
        types_balance=get_primitive_from_metadata("Balance", metadata),
        types_index=get_primitive_from_metadata("AccountInfo", metadata, ),
        types_phase=get_path_from_metadata("Phase", metadata),
        types_address=get_path_from_metadata("Address", metadata),
        types_extrinsicSignature=get_current_path_from_metadata(
            "MultiSignature", metadata
        ),
        types_paraId="polkadot_parachain.primitives.Id",
        types_sp_core_crypto_accountId32="GenericAccountId",
        types_pallet_identity_types_data="Data",
        metadata=metadata,
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


def find_type_in_metadata(name, metadata):
    return_data = []
    for item in find_in_obj(metadata.value[1]["V14"]["types"]["types"], name):
        return_data.append(item)
    return return_data


def get_primitive_from_metadata(name, metadata):
    data = find_type_in_metadata(name, metadata)
    value = metadata.value[1]["V14"]["types"]["types"]
    for path in data[0]:
        if path == "name":
            continue
        value = value[path]
    type_with_primitive = metadata.value[1]["V14"]["types"]["types"][value["type"]]
    return type_with_primitive["type"]["def"]["primitive"]


def get_path_from_metadata(name, metadata):
    data = find_type_in_metadata(name, metadata)
    value = metadata.value[1]["V14"]["types"]["types"]
    for path in data[0]:
        if path in ("typeName", "name"):
            continue
        value = value[path]
    type_with_primitive = metadata.value[1]["V14"]["types"]["types"][value["type"]]
    returned_path = ".".join(str(x) for x in type_with_primitive["type"]["path"])
    return returned_path


def get_current_path_from_metadata(name, metadata):
    data = find_type_in_metadata(name, metadata)
    value = metadata.value[1]["V14"]["types"]["types"]
    for path in data[0]:
        if path == "path":
            value = value[path]
            returned_path = ".".join(str(x) for x in value)
            return returned_path
        value = value[path]
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


def main():
    try:
        substrate = SubstrateInterface(url=url)
    except ConnectionRefusedError:
        print("⚠️ Can't connect by {url}, check it is available?")
        exit()

    json_metadata = get_metada_param(substrate)

    jsonStr = json.dumps(json_metadata.__dict__)
    print(jsonStr)


if __name__ == "__main__":
    main()
