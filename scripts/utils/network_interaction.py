from substrateinterface import SubstrateInterface


def create_connection_by_url(url) -> SubstrateInterface:
    try:
        substrate = SubstrateInterface(
            url=url, use_remote_preset=True, ws_options={
                "auto_reconnect": True,
                "reconnect_interval": 5,
                "max_reconnects": 10,
                "ping_interval": 10,
                "ping_timeout": 45,
                "pong_timeout": 45,
                "headers": {"Origin": "polkadot.js.org"}
            })
    except Exception as err:
        print(f"⚠️ Can't connect by {url}, check it is available? \n {err}")
        raise

    return substrate
