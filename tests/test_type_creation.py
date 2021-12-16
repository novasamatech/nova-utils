import pytest
from scripts.create_type_file import get_properties, create_connection_by_url, get_metadata_param

test_data = [
    ["wss://rpc.polkadot.io", "Polkadot"],
    ["wss://kusama-rpc.polkadot.io", "Kusama"],
    ["wss://westend-rpc.polkadot.io", "Westend"],
    ["wss://statemine.api.onfinality.io/public-ws", "Statemine"],
    ["wss://karura-rpc-0.aca-api.network", "Karura"],
    ["wss://rpc.shiden.astar.network", "Shiden"],
    ["wss://bifrost-rpc.liebi.com/ws", "Bifrost"],
    ["wss://heiko-rpc.parallel.fi", "Parallel Heiko"],
    ["wss://basilisk.api.onfinality.io/public-ws", "Basilisk"],
    ["wss://fullnode.altair.centrifuge.io", "Altair"],
    ["wss://spiritnet.kilt.io/", "KILT Spiritnet"],
    ["wss://kilt-peregrine-k8s.kilt.io", "KILT Peregrine"],
    ["wss://falafel.calamari.systems/", "Calamari Parachain"],
    ["wss://quartz.unique.network", "QUARTZ by UNIQUE"],
    ["wss://pioneer.api.onfinality.io/public-ws", "Pioneer Network"]
]

@pytest.mark.parametrize("url, expected", test_data)
def test_properties(url, expected):
    network_property = get_properties(create_connection_by_url(url))
    assert network_property.name == expected


@pytest.mark.parametrize("url, expected", test_data)
def test_type_building(url, expected):
    network_types = get_metadata_param(create_connection_by_url(url))
    assert isinstance(network_types.runtime_id, int)