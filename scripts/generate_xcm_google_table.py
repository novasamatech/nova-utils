import csv
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

from utils.useful_functions import parse_json_file
from utils.data_model.xcm_json_model import XcmJson
from utils.useful_functions import find_chain_by_id

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credential_json = os.getenv('GOOGLE_API_CREDENTIALS')
SPREADSHEET_TITLE = 'xcm-list'

csv_file_path = './csv_xcm_data.csv'
xcm_version = 'v2'
chains_version = 'v4'


def build_array_of_xcm_data(xcm_object, chains_json, chains_array, marker):
    """That function generate array for each network in xcm_object.chains with all tokens and supported destinations

    Args:
        xcm_object (XcmJson): Object created from xcm/transfers.json
        chains_json (json): Parsed json file with chains from chains/vX/chains_dev.json
        chains_array (List): List of availabe chains for creating data
        marker (str): marker which will add to chain

    Returns:
        List[]: [['Polkadot', 'DOT', '', '', 'marker']]
    """
    xcm_data_array = []

    for network in xcm_object.chains:
            chain = find_chain_by_id(chains_json, network.chainId)
            data = [chain.name]
            for asset in network.assets:
                data.append(asset.assetLocation)
                accumulator = ['']*len(chains_array)
                for destination in asset.xcmTransfers:
                    for idx, filable_chain in enumerate(chains_array):
                        if filable_chain == find_chain_by_id(chains_json, destination.destination.chainId).name:
                            accumulator[idx] = marker

                for id in accumulator: data.append(id)
                xcm_data_array.append(data)
                data = [chain.name]

    return xcm_data_array


def merge_dev_and_prod_data(dev_data, prod_data):
    for dev_id, dev_row in enumerate(dev_data):
        for prod_id, prod_row in enumerate(prod_data):
            if (prod_row[0] == dev_row[0] and prod_row[1] == dev_row[1]):
                for idx, element in enumerate(prod_row):
                    if (prod_row[idx] == 'prod'):
                        dev_data[dev_id][idx] = prod_row[idx]
    return dev_data


def prepare_data_to_push_in_csv(chains, dev_xcm_path, prod_xcm_path, dev_chains_path, prod_chains_path):

    dev_xcm_obj = XcmJson(**parse_json_file(dev_xcm_path))
    prod_xcm_obj = XcmJson(**parse_json_file(prod_xcm_path))

    dev_chains_json = parse_json_file(dev_chains_path)
    prod_chains_json = parse_json_file(prod_chains_path)

    dev_data = build_array_of_xcm_data(dev_xcm_obj, dev_chains_json, chains, 'dev')
    prod_data = build_array_of_xcm_data(prod_xcm_obj, prod_chains_json, chains, 'prod')

    merged_data = merge_dev_and_prod_data(dev_data, prod_data)

    return merged_data


def create_csv_data_representation(xcm_object: XcmJson, csv_file_path: str):
    """That function create csv file with data from prod and dev available xcm transfers

    Args:
        xcm_object (XcmJson): Object created from xcm/transfers.json
        csv_file_path (str): path to the file to be created
    """

    chains_json = parse_json_file(f'./chains/{chains_version}/chains_dev.json')
    chains = []
    for network in xcm_object.chains:
        chains.append(find_chain_by_id(chains_json, network.chainId).name)
    chains.sort()

    header = ['Network', 'Token']
    for chain_name in chains: header.append(chain_name)

    with open(csv_file_path, 'w') as f:
        writer = csv.writer(f)

        writer.writerow(header)
        csv_rows = prepare_data_to_push_in_csv(
            chains,
            f'./xcm/{xcm_version}/transfers_dev.json',
            f'./xcm/{xcm_version}/transfers.json',
            f'./chains/{chains_version}/chains_dev.json',
            f'./chains/{chains_version}/chains.json'
        )

        for row in csv_rows : writer.writerow(row)


def push_sheet_to_google(csv_data, spreadsheet_title):
    """That function will push csv data to the google drive via google sheet api

    Args:
        csv_data: CSV data file
        spreadsheet_title: File title to be updated
    """

    credentials = ServiceAccountCredentials._from_parsed_json_keyfile(json.loads(credential_json), SCOPES)
    client = gspread.authorize(credentials)

    spreadsheet = client.open(spreadsheet_title)

    client.import_csv(spreadsheet.id, data=csv_data)


def main():
    """
    That script collect data from xcm/transfers.json and xcm/transfers_dev.json, next build the csv file with all available directions.

    1. Create a xcm object
    2. Generate csv data file
    3. Push csv to google sheet
    """

    xcm_object = XcmJson(**parse_json_file(f'./xcm/{xcm_version}/transfers_dev.json'))
    create_csv_data_representation(xcm_object, csv_file_path)

    with open(csv_file_path, 'r') as f:
        csv_data_file = f.read()
        push_sheet_to_google(csv_data_file, SPREADSHEET_TITLE)


if __name__ == '__main__':
    main()
