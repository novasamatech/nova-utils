import os
import json

from utils.work_with_data import replace_data_in_nested_object, get_data_from_file, write_data_to_file


env = os.getenv('ENVIRONMENT')
new_domain = 'https://config2.novasama.uz/'
value_to_replace = 'https://raw.githubusercontent.com/nova-wallet/nova-utils/master/'

if env == 'DEV':
    chains_file_path = os.getenv('DEV_CHAINS_JSON_PATH')
    assets_file_path = os.getenv('DEV_ASSETS_JSON_PATH')
elif env == 'PROD':
    chains_file_path = os.getenv('CHAINS_JSON_PATH')
    assets_file_path = os.getenv('ASSETS_JSON_PATH')
else:
    raise Exception(f'Provide right ENVIRONMENT variable - DEV or PROD, currentli it is: {env}')

replaced_chains_file_path = chains_file_path # Temporarly update the same file as provided
replaced_assets_file_path = assets_file_path

chains_data = get_data_from_file(chains_file_path)
assets_data = get_data_from_file(assets_file_path)

replace_data_in_nested_object(chains_data, value_to_replace, new_domain)
replace_data_in_nested_object(assets_data, value_to_replace, new_domain)

write_data_to_file(replaced_chains_file_path, json.dumps(chains_data, indent=4))
write_data_to_file(replaced_assets_file_path, json.dumps(assets_data, indent=4))
