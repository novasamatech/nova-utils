import os
import json
import requests


def get_request_via_https(url) -> json:
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as request_error:
        raise SystemExit(request_error)


def get_network_list(path):

    dn = os.path.abspath('./')
    try:
        with open(dn + path) as fin:
            chains_data = json.load(fin)
    except:
        raise

    return chains_data


def get_data_from_file(file_path):
    with open(file_path, encoding='UTF-8') as fin:
        return json.load(fin)


def write_data_to_file(name, data: str):

    with open(name, "w") as file:
        file.write(data)
        file.write("\n")
