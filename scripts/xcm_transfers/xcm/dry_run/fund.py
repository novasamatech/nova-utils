from scalecodec import GenericCall
from substrateinterface import SubstrateInterface

from scripts.utils.chain_model import StatemineAssetType, OrmlAssetType, ChainAsset, NativeAssetType
from scripts.xcm_transfers.utils.account_id import multi_address
from scripts.xcm_transfers.xcm.dry_run.dispatch_as import compose_dispatch_as
from scripts.xcm_transfers.xcm.dry_run.origins import signed_origin
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain


def compose_native_fund(
        substrate: SubstrateInterface,
        chain: XcmChain,
        account: str,
        amount_planks: int,
) -> GenericCall:
    return substrate.compose_call(
        call_module="Balances",
        call_function="force_set_balance",
        call_params={
            "who": multi_address(account, chain.chain.has_evm_addresses()),
            "new_free": amount_planks
        }
    )


def compose_assets_fund(
        substrate: SubstrateInterface,
        chain: XcmChain,
        statemine_type: StatemineAssetType,
        account: str,
        amount_planks: int,
) -> GenericCall:
    asset_info = substrate.query(module=statemine_type.pallet_name(), storage_function="Asset",
                                 params=[statemine_type.encodable_asset_id()]).value
    issuer = asset_info["issuer"]

    mint_call = substrate.compose_call(
        call_module=statemine_type.pallet_name(),
        call_function="mint",
        call_params={
            "id": statemine_type.encodable_asset_id(),
            "beneficiary": multi_address(account, chain.chain.has_evm_addresses()),
            "amount": amount_planks
        }
    )

    return compose_dispatch_as(
        substrate=substrate,
        origin=signed_origin(issuer),
        call=mint_call
    )


def compose_orml_fund(
        substrate: SubstrateInterface,
        chain: XcmChain,
        orml_type: OrmlAssetType,
        account: str,
        amount_planks: int,
) -> GenericCall:
    return substrate.compose_call(
        call_module=orml_type.pallet_name(),
        call_function="set_balance",
        call_params={
            "who": multi_address(account, chain.chain.has_evm_addresses()),
            "currency_id": orml_type.encodable_asset_id(),
            "new_free": amount_planks,
            "new_reserved": 0,
        }
    )


def compose_fund_call(
        substrate: SubstrateInterface,
        chain: XcmChain,
        chain_asset: ChainAsset,
        account: str,
        amount_planks: int,
) -> GenericCall:
    match chain_asset.type:
        case NativeAssetType():
            return compose_native_fund(substrate, chain, account, amount_planks)
        case StatemineAssetType() as statemineType:
            return compose_assets_fund(substrate, chain, statemineType, account, amount_planks)
        case OrmlAssetType() as ormlType:
            return compose_orml_fund(substrate, chain, ormlType, account, amount_planks)

        case UnsupportedAssetType():
            raise Exception("Unsupported asset type")


def fund_account_and_then(
        substrate: SubstrateInterface,
        chain: XcmChain,
        chain_asset: ChainAsset,
        account: str,
        amount: int,
        next_call: GenericCall
) -> GenericCall:
    planks_in_sending_asset = chain_asset.planks(amount)

    calls = []

    fund_sending_asset_call = compose_fund_call(substrate, chain, chain_asset, account, planks_in_sending_asset)
    calls.append(fund_sending_asset_call)

    utility_asset = chain.chain.get_utility_asset()
    if utility_asset.id != chain_asset.id:
        planks_in_utility_asset = utility_asset.planks(amount)
        fund_utility_asset_call = compose_fund_call(substrate, chain, utility_asset, account, planks_in_utility_asset)
        calls.append(fund_utility_asset_call)

    wrapped_next_call = compose_dispatch_as(
        substrate=substrate,
        origin=signed_origin(account),
        call=next_call
    )
    calls.append(wrapped_next_call)

    return substrate.compose_call(
        call_module="Utility",
        call_function="batch_all",
        call_params={
            "calls": calls
        }
    )