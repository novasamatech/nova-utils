from scalecodec import ss58_decode

from scripts.utils.chain_model import Chain


def decode_account_id(address: str) -> str:
    if address.startswith("0x"):
        # Handles both evm addresses and cases when already decoded account id is passed
        return address.lower()
    else:
        return "0x" + ss58_decode(address)
