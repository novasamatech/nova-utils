from scripts.utils.chain_model import StatemineAssetType
from scripts.xcm_transfers.xcm.dry_run.events.deposit import find_deposit_amount

RECIPIENT = "13mp1WEs72kbCBF3WKcoK6Hfhu2HHZGpQ4jsKCZbfd6FoRvH"
OTHER_ACCOUNT = "13dfnsTFnS8AVefNUx6RQThDRzA3NCqyb1tK7MiVHDuPXJqa"


class _StubChain:
    def access_substrate(self, _action):
        raise AssertionError("asset id matching must not touch the chain")


class _StatemineAsset:
    def __init__(self):
        self.type = StatemineAssetType({"assetId": "0x0201090704", "palletName": "ForeignAssets"}, _StubChain())

    @staticmethod
    def amount(planks: int) -> float:
        return planks / 10 ** 18


def _event(pallet: str, name: str, attributes: dict) -> dict:
    return {"module_id": pallet, "event_id": name, "attributes": attributes}


def test_finds_issued_deposit_for_recipient():
    events = [
        _event("ForeignAssets", "Issued", {"owner": OTHER_ACCOUNT, "amount": 1}),
        _event("ForeignAssets", "Issued", {"owner": RECIPIENT, "amount": 2 * 10 ** 18}),
    ]

    assert find_deposit_amount(events, _StatemineAsset(), RECIPIENT) == 2.0


# Snowbridge assets withdrawn back to Asset Hub move from a sovereign account, so pallet-assets emits Deposited
def test_finds_deposited_event_when_nothing_was_issued():
    events = [
        _event("ForeignAssets", "Withdrawn", {"who": OTHER_ACCOUNT, "amount": 3 * 10 ** 18}),
        _event("ForeignAssets", "Deposited", {"who": OTHER_ACCOUNT, "amount": 10 ** 18}),
        _event("ForeignAssets", "Deposited", {"who": RECIPIENT, "amount": 3 * 10 ** 18}),
    ]

    assert find_deposit_amount(events, _StatemineAsset(), RECIPIENT) == 3.0


def test_returns_none_without_deposit_to_recipient():
    events = [_event("ForeignAssets", "Deposited", {"who": OTHER_ACCOUNT, "amount": 10 ** 18})]

    assert find_deposit_amount(events, _StatemineAsset(), RECIPIENT) is None
