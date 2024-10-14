import requests
from typing import List

payload = "{\"query\":\"query{\\n  _metadata{\\n    chain\\n    lastProcessedHeight\\n    targetHeight\\n  }\\n}\",\"variables\":{}}"
headers = {
    'Host': 'gateway.subquery.network',
    'Connection': 'Keep-Alive',
    'User-Agent': 'okhttp/4.11.0',
    'Content-Type': 'application/json; charset=UTF-8'
}


def test_subquery_is_synced(subquery_projects):
    for url in subquery_projects:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            last_processed_height = response.json().get('data').get('_metadata').get('lastProcessedHeight')
            target_height = response.json().get('data').get('_metadata').get('targetHeight')
            assert abs(target_height - last_processed_height) < 10
