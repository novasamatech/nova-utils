def signed_origin(account: str) -> dict:
    return {"system": {"Signed": account}}


def root_origin() -> dict:
    return {"system": "Root"}
