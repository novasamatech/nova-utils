from utils.data_model.chain_json_model import Chain
from utils.useful_functions import create_connection_by_url, deep_search_in_object

WEIGHT_PER_SECOND = 1_000_000_000_000
WEIGHT_PER_MILLIS = WEIGHT_PER_SECOND / 1000  # 1_000_000_000
WEIGHT_PER_MICROS = WEIGHT_PER_MILLIS / 1000  # 1_000_000
WEIGHT_PER_NANOS = WEIGHT_PER_MICROS / 1000  # 1_000


def base_fee_per_second(ExtrinsicBaseWeight):
    base_weight = ((ExtrinsicBaseWeight / WEIGHT_PER_NANOS)
                   * WEIGHT_PER_SECOND) / WEIGHT_PER_MILLIS

    base_tx_per_second = WEIGHT_PER_SECOND / base_weight
    return base_tx_per_second


def connect_to_node(chain: Chain):
    for node in chain.nodes:
        connection = create_connection_by_url(node.get('url'))
        if (connection):
            return connection


def get_base_weight_from_chain(chain: Chain):
    connection = connect_to_node(chain)
    weight = connection.get_constant('System', 'BlockWeights').value
    print(weight)
    return weight.get('per_class').get('normal').get('base_extrinsic')


def biforst_base_fee(chain: Chain) -> float:

    ExtrinsicBaseWeight = get_base_weight_from_chain(chain)

    base_tx_per_second = base_fee_per_second(ExtrinsicBaseWeight)

    fee_per_second = base_tx_per_second * WEIGHT_PER_MILLIS

    return fee_per_second


def heiko_base_fee(chain) -> float:

    ExtrinsicBaseWeight = get_base_weight_from_chain(chain)

    base_tx_per_second = base_fee_per_second(ExtrinsicBaseWeight)

    fee_per_second = base_tx_per_second * WEIGHT_PER_MILLIS

    return fee_per_second


def kintsugi_base_fee(chain):

    def base_tx_in_ksm():
        ksm = 1*10**12
        return ksm / 50_000

    ExtrinsicBaseWeight = get_base_weight_from_chain(chain)

    base_tx_per_second = base_fee_per_second(ExtrinsicBaseWeight)

    return base_tx_per_second * base_tx_in_ksm()


def karura_base_fee(chain):

    ExtrinsicBaseWeight = get_base_weight_from_chain(chain)

    def base_tx_in_kar():
        return WEIGHT_PER_MILLIS

    base_tx_per_second = base_fee_per_second(ExtrinsicBaseWeight)

    return base_tx_per_second * base_tx_in_kar()


def turing_base_fee(chain):

    ExtrinsicBaseWeight = get_base_weight_from_chain(chain)

    def ksm_per_second():
        # CurrencyId::KSM.cent() * 16
        ksm = 1*10**12 / 10
        return ksm * 16

    base_tx_per_second = base_fee_per_second(ExtrinsicBaseWeight)

    return base_tx_per_second * ksm_per_second()


def moonriver_fee_calculation(chain, xcm_asset):

    connection = connect_to_node(chain)

    query_map = connection.query_map(
        'AssetManager', 'AssetTypeUnitsPerSecond', [])

    for query_item in query_map:
        paraId = xcm_asset.get('multiLocation').get('parachainId')
        if(deep_search_in_object(query_item[0].serialize(), 'Parachain', paraId)):
            return query_item[1].value
