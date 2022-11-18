from substrateinterface import SubstrateInterface, Keypair

def metadata_is_v14(metadata):
    if "V14" in metadata.value[1].keys():
        return True
    else:
        raise Exception("It's not a v14 runtime: %s" % (metadata.value[1].keys()))


def account_does_not_need_updates(substrate: SubstrateInterface):
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
