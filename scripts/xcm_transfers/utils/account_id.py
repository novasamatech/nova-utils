from scalecodec import ss58_decode


def decode_account_id(address: str) -> str:
    if address.startswith("0x"):
        # Handles both evm addresses and cases when already decoded account id is passed
        return address.lower()
    else:
        return "0x" + ss58_decode(address)

def multi_address(account: str, evm: bool):
    if evm:
        return account
    else:
        return {"Id": account}
