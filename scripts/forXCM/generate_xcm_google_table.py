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
        current_xcm.append(xcm.chainName)
        destinations = []
        for asset in xcm.assets:
            destinations.append(asset.get('asset') + ' -> ' +
                                ','.join(asset.get('destination')))
        current_xcm.append('<br/>'.join(destinations))
        returning_array.append(current_xcm)
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


def update_values(creds, spreadsheet_id, range_name, value_input_option,
                  _values):
    try:

        service = build('sheets', 'v4', credentials=creds)
        values = [
            [
                # Cell values ...
            ],
            # Additional rows ...
        ]
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
    # create_spreadsheet(creds)
    data = generate_value_matrix()
    update_values(creds, SPREADSHEET_ID,
                  RANGE_NAME, "USER_ENTERED", data)
