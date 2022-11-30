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
    try:
        substrate = SubstrateInterface(
                url=url, use_remote_preset=use_remote_preset, ws_options=ws_otpions
            )
    except Exception as err:
        print(f"⚠️ Can't connect by {url}, check it is available? \n {err}")
        raise

    return substrate
