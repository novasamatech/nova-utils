from utils.data_model.chain_json_model import Chain
from utils.useful_functions import create_connection_by_url, deep_search_in_object

WEIGHT_PER_SECOND = 1_000_000_000_000
WEIGHT_PER_MILLIS = WEIGHT_PER_SECOND / 1000  # 1_000_000_000
WEIGHT_PER_MICROS = WEIGHT_PER_MILLIS / 1000  # 1_000_000
WEIGHT_PER_NANOS = WEIGHT_PER_MICROS / 1000  # 1_000


def base_tx_per_second(base_weight):
    fee_per_second = WEIGHT_PER_SECOND / base_weight
    return fee_per_second


def connect_to_node(chain: Chain):
    for node in chain.nodes:
        connection = create_connection_by_url(node.get('url'))
        if (connection):
            return connection


def get_base_weight_from_chain(chain: Chain):
    connection = connect_to_node(chain)
    weight = connection.get_constant('System', 'BlockWeights').value

    return weight.get('per_class').get('normal').get('base_extrinsic')


def biforst_base_fee(chain: Chain) -> float:

    base_weight = get_base_weight_from_chain(chain)

    base_fee_in_ksm = base_tx_per_second(base_weight) * WEIGHT_PER_MILLIS

    return base_fee_in_ksm


def heiko_base_fee(chain) -> float:
    '''
    https://github.com/parallel-finance/parallel/blob/b72d6afd263086d89d5256b571e522113ebde59f/runtime/heiko/src/constants.rs#L86
    let base_weight = Balance::from(base_weight::get());
        let base_tx_per_second = (WEIGHT_PER_SECOND as u128) / base_weight;
        let hko_per_second = base_tx_per_second * super::currency::CENTS / 10;
        hko_per_second / 50 //almost 250_000_000_000~=1/4 WEIGHT_PER_SECOND in polkadot-v0.9.24
    }

    https://github.com/parallel-finance/parallel/blob/b72d6afd263086d89d5256b571e522113ebde59f/runtime/heiko/src/constants.rs#L19
    pub const MILLICENTS: Balance = 10_000_000;
    pub const CENTS: Balance = 1_000 * MILLICENTS
    '''

    base_weight = get_base_weight_from_chain(chain)

    hko_per_second = base_tx_per_second(base_weight) * 10_000_000_000 / 10

    base_fee_in_ksm = hko_per_second / 50

    return base_fee_in_ksm


def kintsugi_base_fee(chain):

    def base_tx_in_ksm():
        ksm = 1*10**12
        return ksm / 50_000

    base_weight = get_base_weight_from_chain(chain)

    base_fee_in_ksm = base_tx_per_second(base_weight) * base_tx_in_ksm()

    return base_fee_in_ksm


def karura_base_fee(chain):

    base_weight = get_base_weight_from_chain(chain)

    base_fee_in_kar = base_tx_per_second(base_weight) * WEIGHT_PER_MILLIS

    return base_fee_in_kar


def turing_base_fee(chain):

    base_weight = get_base_weight_from_chain(chain)

    def ksm_per_second():
        '''
        https://github.com/OAK-Foundation/OAK-blockchain/blob/master/runtime/turing/src/xcm_config.rs#L182
        '''
        # CurrencyId::KSM.cent() * 16
        ksm = 1*10**12 / 10
        return ksm * 16

    base_fee_in_ksm = ksm_per_second()

    return base_fee_in_ksm


def moonriver_fee_calculation(chain, xcm_asset):

    connection = connect_to_node(chain)

    query_map = connection.query_map(
        'AssetManager', 'AssetTypeUnitsPerSecond', [])

    for query_item in query_map:
        paraId = xcm_asset.get('multiLocation').get('parachainId')
        if(deep_search_in_object(query_item[0].serialize(), 'Parachain', paraId)):
            return query_item[1].value
