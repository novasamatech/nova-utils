import json
import pytest
from scripts.utils.substrate_interface import create_connection_by_url
from scripts.create_type_file import get_metadata_param, get_properties

test_data = [
    ["wss://rpc.polkadot.io", "Polkadot", "chains/v2/types/polkadot.json"],
    ["wss://kusama-rpc.polkadot.io", "Kusama", "chains/v2/types/kusama.json"],
    ["wss://westend-rpc.polkadot.io", "Westend", "chains/v2/types/westend.json"],
    ["wss://statemine.api.onfinality.io/public-ws", "Statemine", "chains/v2/types/statemine.json"],
    ["wss://karura-rpc-0.aca-api.network", "Karura", "chains/v2/types/karura.json"],
    ["wss://rpc.shiden.astar.network", "Shiden", "chains/v2/types/shiden.json"],
    ["wss://bifrost-rpc.liebi.com/ws", "Bifrost", "chains/v2/types/bifrost.json"],
    ["wss://heiko-rpc.parallel.fi", "Parallel Heiko", "chains/v2/types/parallel_heiko.json"],
    ["wss://basilisk.api.onfinality.io/public-ws", "Basilisk", "chains/v2/types/basilisk.json"],
    ["wss://fullnode.altair.centrifuge.io", "Altair", "chains/v2/types/altair.json"],
    ["wss://spiritnet.kilt.io/", "KILT Spiritnet", "chains/v2/types/kilt_spiritnet.json"],
    ["wss://peregrine.kilt.io/parachain-public-ws/", "KILT Peregrine", "chains/v2/types/kilt_peregrine.json"],
    ["wss://falafel.calamari.systems/", "Calamari Parachain", "chains/v2/types/calamari.json"],
    ["wss://quartz.unique.network", "QUARTZ by UNIQUE", "chains/v2/types/quartz.json"],
    ["wss://pioneer.api.onfinality.io/public-ws", "Pioneer Network", "chains/v2/types/bit.country_pioneer.json"],
    ["wss://asia-ws.unique.network/", "UNIQUE", "chains/v2/types/unique.json"]
]

@pytest.mark.parametrize("url, expected, types_path", test_data)
def test_properties(url, expected, types_path):
    network_property = get_properties(create_connection_by_url(url))
    assert network_property.name == expected


@pytest.mark.parametrize("url, name, types_path", test_data)
def test_type_building(url, name, types_path):
    network_types = get_metadata_param(create_connection_by_url(url))
    with open(types_path, "r") as file:
        property = json.loads(file.read())
        for key, value in network_types.types.items():
            assert value == property.get('types').get(key)
    assert isinstance(network_types.runtime_id, int)