from substrateinterface import SubstrateInterface


def create_connection_by_url(url):
    try:
        substrate = SubstrateInterface(
            url=url, use_remote_preset=True, ws_options={
                "auto_reconnect": True,
                "reconnect_interval": 5,
                "max_reconnects": 10,
                "ping_interval": 5,
                "ping_timeout": 5,
                "pong_timeout": 5,
                "headers": {"Origin": "polkadot.js.org"}
            })
    except Exception as err:
        print(f"⚠️ Can't connect by {url}, check it is available? \n {err}")
        raise

    return substrate