import os
import json

def replace_data_in_nested_object(json_data, value_to_replace, new_value):
    """
    Recursively replaces value in any parameter of dictionaries with new_value.
    """
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            if isinstance(value, (dict, list)):
                replace_data_in_nested_object(value, value_to_replace, new_value)
            elif isinstance(value, str) and value_to_replace in value:
                json_data[key] = value.replace(value_to_replace, new_value)
    elif isinstance(json_data, list):
        for item in json_data:
            replace_data_in_nested_object(item, value_to_replace, new_value)


if __name__ == '__main__':
    env = os.getenv('ENVIRONMENT')
    new_domain = 'https://config2.novasama.uz/'
    value_to_replace = 'https://raw.githubusercontent.com/nova-wallet/nova-utils/master/'

    if env == 'DEV':
        chains_file_path = os.getenv('DEV_CHAINS_JSON_PATH')
    elif env == 'PROD':
        chains_file_path = os.getenv('CHAINS_JSON_PATH')
    else:
        raise Exception(f'Provide right ENVIRONMENT variable - DEV or PROD, currentli it is: {env}')

    replaced_file_path = chains_file_path # Temporarly update the same file as provided

    with open(chains_file_path, 'r') as f:
        data = json.load(f)

    replace_data_in_nested_object(data, new_domain)

    with open(replaced_file_path, 'w') as f:
        f.write(json.dumps(data, indent=4))
