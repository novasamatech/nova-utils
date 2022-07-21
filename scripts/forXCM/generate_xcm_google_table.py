from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.xcm_сhain import XcmChain
from utils.useful_functions import parse_json_file

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1ymlOS8TL6Ka4Qk4nZAM1KXThH1UM2TRSzUaYfbRdc_A'
RANGE_NAME = 'Лист1'

CREDENTIALS_FILE = './scripts/forXCM/credentials.json'
SPREADSHEET_TITLE = "Cross-chain transfers"
xcm_json_path = './xcm/v2/transfers_dev.json'
chains_json_path = './chains/v4/chains_dev.json'


def set_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def create_spreadsheet(creds):
    try:
        service = build('sheets', 'v4', credentials=creds)
        spreadsheet = {
            'properties': {
                'title': SPREADSHEET_TITLE
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
        return spreadsheet.get('spreadsheetId')
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


def generate_value_matrix():
    returning_array = []
    xcm_data = build_data_from_jsons()
    for xcm in xcm_data:
        current_xcm = []
        destinations = generate_headers()
        for asset in xcm.assets:
            current_xcm.append(xcm.chainName)
            current_xcm.append(asset.get('asset'))
            asset_destinations = asset.get('destination')
            for asset_destination in asset_destinations:
                # TODO fix one asset with more destinations
                for destination_id in range(3, len(destinations)):
                    if destinations[destination_id] == asset_destination:
                        current_xcm.append("->")
                    else:
                        current_xcm.append("")
            returning_array.append(current_xcm)
            current_xcm = []
    returning_array.sort()
    increment = iter(range(1, len(returning_array) + 1))
    [network.insert(0, next(increment)) for network in returning_array]
    return returning_array


def build_data_from_jsons():
    xcm_json_data = parse_json_file(xcm_json_path)
    chains_json_data = parse_json_file(chains_json_path)
    processed_xcm_chains = []
    for xcm in xcm_json_data.get('chains'):
        processed_xcm_chains.append(XcmChain(xcm, chains_json_data))
    return processed_xcm_chains


def generate_headers():
    returning_array = []
    xcm_data = build_data_from_jsons()
    for i in range(3):
        returning_array.append("")
    for xcm in xcm_data:
        for asset in xcm.assets:
            destinations = asset.get('destination')
            for destination in destinations:
                if destination not in returning_array:
                    returning_array.append(destination)
    returning_array.sort()
    return returning_array


def update_values(creds, spreadsheet_id, range_name, value_input_option,
                  values):
    try:
        service = build('sheets', 'v4', credentials=creds)
        body = {
            'values': values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


if __name__ == '__main__':
    creds = set_credentials()
    # create_spreadsheet(creds) TODO create if present in directory
    headers = generate_headers()
    body = generate_value_matrix()
    body.insert(0, headers)
    update_values(creds, SPREADSHEET_ID,
                  RANGE_NAME, "USER_ENTERED", body)
