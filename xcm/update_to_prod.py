import json

def convert_list_to_dict(lst, key_name):
    return_dict = {}
    for _, item in enumerate(lst):
        if key_name == 'xcmTransfers':
            return_dict[item["destination"]["chainId"]] = item
        else:
            return_dict[item[key_name]] = item
    return return_dict

def convert_dict_to_list(dct):
    return [element for element in dct]

def compare_data(data1, data2, path="", check_modes=True, add_keys=True):
    """
    Recursively compare data1 and data2 dictionaries and prints the
    differences to the console. Returns a dictionary of updates.
    """
    updates = {}
    for key, value1 in data1.items():
        value2 = data2.get(key)
        new_path = path + "/" + key if path else key
        if 'networkBaseWeight' in new_path.split('/'):
            continue
        if 'assetsLocation' in new_path.split('/'):
            continue
        if 'instructions' in new_path.split('/'):
            continue
        if isinstance(value1, dict) and isinstance(value2, dict):
            nested_updates = compare_data(value1, value2, new_path, check_modes, add_keys)
            if nested_updates:
                updates.update(nested_updates)
        elif isinstance(value1, list) and isinstance(value2, list):
            if key == 'chains':
                key_name = 'chainId'
            elif key == 'assets':
                key_name = 'assetLocation'
            elif key == 'xcmTransfers':
                key_name = 'xcmTransfers'
            else:
                raise KeyError(f'List {key} is unknown, please add maping to convert it to dict.')

            dict1 = convert_list_to_dict(value1, key_name)
            dict2 = convert_list_to_dict(value2, key_name)
            for i, item in dict1.items():
                if i not in dict2:
                    if add_keys:
                        dict2[i] = {}
                    else:
                        continue
                nested_updates = compare_data(item, dict2[i], f"{new_path}[{i}]", check_modes, add_keys)
                if nested_updates:
                    updates.update(nested_updates)
            if len(dict1) != len(dict2):
                print(f"\nData in file_1.json has a different number of items than in xcm/v2/transfers.json for {new_path}")
                print(f"File 1 items: {len(dict1)}")
                print(f"File 2 items: {len(dict2)}")
                if add_keys:
                    update = input("Which value should be updated in xcm/v2/transfers.json? (y/n) ")
                    if update.lower() == 'y':
                        updates[new_path] = value1
                    dict2.update({i: None for i in range(len(dict2), len(dict1))})
            value1 = convert_dict_to_list(dict1)
            value2 = convert_dict_to_list(dict2)
        elif value2 != value1:
            if check_modes is False and 'mode' in new_path.split('/'):
                continue
            print(f"Data in file_1.json updated for {new_path}")
            print(f"Old value: {value2}")
            print(f"New value: {value1}")
            update = input("Which value should be updated in xcm/v2/transfers.json? (y/n) ")
            if update.lower() == 'y':
                updates[new_path] = value1
    return updates


# Read data from file_1.json and file_2.json
with open('xcm/v2/transfers_dev.json') as f:
    data1 = json.load(f)
with open('xcm/v2/transfers.json') as f:
    data2 = json.load(f)

# Ask for mode of operation
mode = input("Enter mode of operation (1 = check all changes, 2 = skip 'mode' paths): ")
if mode == '1':
    check_modes = True
elif mode == '2':
    check_modes = False
else:
    print("Invalid mode selected. Defaulting to mode 1 (check all changes).")
    check_modes = True

# Compare the data in the two files
updates = compare_data(data1, data2, check_modes=check_modes)

# Update xcm/v2/transfers.json
if updates:
    for key, value in updates.items():
        keys = key.split("/")
        obj = data2
        for k in keys[:-1]:
            obj = obj[k]
        obj[keys[-1]] = value
    with open('xcm/v2/transfers.json', 'w') as f:
        json.dump(data2, f, indent=4)
        print("Data updated in xcm/v2/transfers.json")
else:
    print("No updates needed")
