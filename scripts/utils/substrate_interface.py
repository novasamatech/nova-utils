#!/usr/bin/env python3
"""That script is used for creating substrate connection for all other scripts"""

from substrateinterface import SubstrateInterface

default_ws_options = {
    "auto_reconnect": True,
    "reconnect_interval": 5,
    "max_reconnects": 5,
    "ping_interval": 5,
    "ping_timeout": 10,
    "pong_timeout": 10,
    "headers": {"Origin": "polkadot.js.org"}
}

def create_connection_by_url(url, use_remote_preset=False, ws_otpions=default_ws_options) -> SubstrateInterface:
    """Returns substrate interface object

    Args:
        url (str): Websocket url
        use_remote_preset (bool, optional): When True preset is downloaded from Github master
            of https://github.com/polkascan/py-substrate-interface. Defaults to False.
        ws_otpions (obj, optional): Parameters for websocket connection itself.
            Defaults to default_ws_options.

    Returns:
        SubstrateInterface: _description_
    """
    try:
        substrate = SubstrateInterface(
                url=url, use_remote_preset=use_remote_preset, ws_options=ws_otpions
            )
    except Exception as err:
        print(f"⚠️ Can't connect by {url}, check it is available? \n {err}")
        raise

    return substrate
