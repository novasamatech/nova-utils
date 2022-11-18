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
    except ConnectionRefusedError and TimeoutError:
        print("⚠️ Can't connect by %s, check it is available?" % (url))
        raise

    return substrate