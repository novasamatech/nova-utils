import csv
from typing import List
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

from utils.useful_functions import parse_json_file
from utils.data_model.xcm_json_model import XcmJson
from utils.data_model.chain_json_model import Chain
from utils.useful_functions import find_chain
from gspread_formatting import *


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
          "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credential_json = os.getenv('GOOGLE_API_CREDENTIALS')
SPREADSHEET_TITLE = 'xcm-list'

csv_file_path = './csv_xcm_data.csv'
xcm_version = 'v2'
chains_version = 'v4'


class XcmAsset:
    symbol: str
    asset_id: int
    possible_destinations: List[str]
    dev_destinations: List[str]
    prod_destinations: List[str]

    def __init__(self, symbol, asset_id):
        self.symbol = symbol
        self.asset_id = asset_id
        self.possible_destinations = []
        self.dev_destinations = []
        self.prod_destinations = []


class XcmDestinations:
    chain_id: str
    parrent_id: str
    chain_name: str
    assets: List[XcmAsset]

    def __init__(self, chain_id, parrent_id, chain_name, assets):
        self.chain_id = chain_id
        self.parrent_id = parrent_id
        self.chain_name = chain_name
        self.assets = assets

    def collect_possible_destinations(self, chain_json):
        for chain in chain_json:

            if (chain.get('chainId') == self.chain_id): # Skip itself from counting
                continue

            if self.parrent_id is None: # Relaychain
                if chain.get('parentId') is None: # Skip relaychain to relaychain direction
                    continue

                if chain.get('parentId') != self.chain_id: # Skip if parachain from another relaychain
                    continue

            else:   # Parachain
                if chain.get('parentId'):
                    if self.parrent_id != chain.get('parentId'): # Skip if parachains have different relaychain
                        continue
                else:
                    if chain.get('chainId') != self.parrent_id: # Skip if current parachain form another relaychain
                        continue

            for asset in self.assets:
                for chain_asset in chain.get('assets'):
                    asset_symbol = re.findall('[A-Z]', asset.symbol)
                    chain_asset = re.findall('[A-Z]', chain_asset.get('symbol'))
                    if ''.join(asset_symbol) == ''.join(chain_asset):
                        asset.possible_destinations.append(
                            chain.get('chainId'))

    def collect_dev_destinations(self, dev_xcm_obj: XcmJson):
        for xcm_chain_source in dev_xcm_obj.chains:
            if (xcm_chain_source.chainId == self.chain_id):
                for asset in self.assets:
                    for xcm_asset in xcm_chain_source.assets:
                        if asset.asset_id == xcm_asset.assetId:
                            asset.dev_destinations = [
                                chain_id.destination.chainId for chain_id in xcm_asset.xcmTransfers]

    def collect_prod_destinations(self, prod_xcm_obj: XcmJson):
        for xcm_chain_source in prod_xcm_obj.chains:
            if (xcm_chain_source.chainId == self.chain_id):
                for asset in self.assets:
                    for xcm_asset in xcm_chain_source.assets:
                        if asset.asset_id == xcm_asset.assetId:
                            asset.prod_destinations = [
                                chain_id.destination.chainId for chain_id in xcm_asset.xcmTransfers]


def prepare_csv_data_array(headers, chain_json, xcm_destinations: List[XcmDestinations]):

    csv_data_array = []
    operating_data = []
    for network in headers:
        operating_data.append({
            "name": network,
            "chainId": find_chain(chain_json, network).chainId
        })

    for xcm in xcm_destinations:
        for asset in xcm.assets:
            if not asset.possible_destinations:
                xcm.assets.remove(asset)

    for xcm in xcm_destinations:
        current_csv_row = []

        for asset in xcm.assets:
            current_csv_row.append(xcm.chain_name)
            current_csv_row.append(asset.symbol)

            for network in operating_data:
                accumulated_data = ''
                for possible_destination in asset.possible_destinations:
                    if possible_destination == network.get('chainId'):
                        accumulated_data = 'possible'
                for dev_destinations in asset.dev_destinations:
                    if dev_destinations == network.get('chainId'):
                        accumulated_data = 'dev'
                for prod_destinations in asset.prod_destinations:
                    if prod_destinations == network.get('chainId'):
                        accumulated_data = 'prod'
                current_csv_row.append(accumulated_data)

            csv_data_array.append(current_csv_row)
            current_csv_row = []
    return csv_data_array


def collect_data_from_all_sorces(
    dev_xcm_path,
    prod_xcm_path,
    dev_chains_path,
) -> List[XcmDestinations]:

    dev_chains_json = parse_json_file(dev_chains_path)
    dev_xcm_obj = XcmJson(**parse_json_file(dev_xcm_path))
    prod_xcm_obj = XcmJson(**parse_json_file(prod_xcm_path))

    xcm_data_array = create_xcm_destinations_object_array(dev_chains_json)

    for chain in xcm_data_array:
        chain.collect_possible_destinations(dev_chains_json)
        chain.collect_dev_destinations(dev_xcm_obj)
        chain.collect_prod_destinations(prod_xcm_obj)

    return xcm_data_array


def create_csv_data_representation(csv_file_path: str):
    """That function create csv file with data from prod and dev available xcm transfers

    Args:
        csv_file_path (str): path to the file to be created
    """

    chains_json = parse_json_file(f'./chains/{chains_version}/chains.json')
    dev_chains_json = parse_json_file(
        f'./chains/{chains_version}/chains_dev.json')
    chains = []
    for network in chains_json:
        chains.append(network.get('name'))
    chains.sort()

    header = ['Network', 'Token']
    for chain_name in chains:
        header.append(chain_name)

    xcm_destinations = collect_data_from_all_sorces(
        f'./xcm/{xcm_version}/transfers_dev.json',
        f'./xcm/{xcm_version}/transfers.json',
        f'./chains/{chains_version}/chains_dev.json',
    )

    csv_rows = prepare_csv_data_array(
        chains, dev_chains_json, xcm_destinations)

    csv_rows.sort()

    with open(csv_file_path, 'w') as f:
        writer = csv.writer(f)

        writer.writerow(header)

        for row in csv_rows:
            writer.writerow(row)


def push_sheet_to_google(csv_data, spreadsheet_title):
    """That function will push csv data to the google drive via google sheet api

    Args:
        csv_data: CSV data file
        spreadsheet_title: File title to be updated
    """

    credentials = ServiceAccountCredentials._from_parsed_json_keyfile(
        json.loads(credential_json), SCOPES)
    client = gspread.authorize(credentials)

    spreadsheet = client.open(spreadsheet_title)

    client.import_csv(spreadsheet.id, data=csv_data)

    format_google_sheet(spreadsheet)

    spreadsheet.get_worksheet(0).insert_row(['added to prod', 'added to dev'])
    spreadsheet.get_worksheet(0).insert_row(['', 'possible to add'])


def format_google_sheet(spreadsheet):
    worksheet = spreadsheet.get_worksheet(0)

    worksheet.format(["1:1", "A:A"], {'textFormat': {'bold': True}})
    worksheet.freeze(1, 2)
    worksheet.format(["1:180"], {"horizontalAlignment": "CENTER"})
    worksheet.set_basic_filter()

    def create_conditional_rule(range, sheet, condition, color):
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range(range, sheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_CONTAINS', condition),
                format=CellFormat(backgroundColor=color)
            )
        )
        return rule

    rules = get_conditional_format_rules(worksheet)
    rules.clear()
    rules.append(create_conditional_rule(
        range='1:180', sheet=worksheet, condition=['dev'], color=Color.fromHex("#fff2cc")))
    rules.append(create_conditional_rule(
        range='1:180', sheet=worksheet, condition=['prod'], color=Color.fromHex("#d9ead3")))
    rules.append(create_conditional_rule(
        range='1:180', sheet=worksheet, condition=['possible'], color=Color.fromHex("#c9daf8")))
    rules.save()


def create_xcm_destinations_object_array(chains_json_data) -> List[XcmDestinations]:
    xcm_destinations_array = []
    for chain in chains_json_data:
        current_chain = Chain(**chain)

        if 'testnet' in current_chain.options:
            continue

        xcm_destinations_array.append(
            XcmDestinations(
                chain_id=current_chain.chainId,
                parrent_id=current_chain.parentId,
                chain_name=current_chain.name,
                assets=[XcmAsset(symbol=asset.symbol, asset_id=asset.assetId)
                        for asset in current_chain.assets]
            ))

    return xcm_destinations_array


def main():
    """
    That script collect data from xcm/transfers.json and xcm/transfers_dev.json, next build the csv file with all available directions.

    1. Create a xcm object
    2. Generate csv data file
    3. Push csv to google sheet
    4. Format google sheet
    """

    create_csv_data_representation(csv_file_path)

    with open(csv_file_path, 'r') as f:
        csv_data_file = f.read()
        push_sheet_to_google(csv_data_file, SPREADSHEET_TITLE)


if __name__ == '__main__':
    main()
