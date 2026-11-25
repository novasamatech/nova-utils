"""Check that no node URL in a chains config carries a provider key.

This repository is public and the clients read it as is, so a key written into a node URL is a
leaked key: anyone can spend its quota. A key that the apps own is written as a placeholder such
as {INFURA_API_KEY}; the apps substitute their built-in value when they open the connection.

Run over one or more chains config paths:

    python3 scripts/check_node_url_keys.py chains/v23/chains.json
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

# A path segment that looks like a credential: long, and mixing letters with digits.
KEY_LIKE_SEGMENT = re.compile(r"^(?=.*\d)(?=.*[A-Za-z])[A-Za-z0-9_-]{20,}$")
KEY_LIKE_QUERY_NAME = re.compile(r"api[_-]?key|token|secret|^key$", re.IGNORECASE)
PLACEHOLDER = re.compile(r"^\{[A-Z0-9_]+\}$")

# Hosts whose keyed URLs were in the configs before this check existed. They are reported as
# warnings and do not fail the check; do not add a host here, remove one when its key is gone.
KNOWN_KEYED_HOSTS = (
    "bsc.getblock.io",
    "gateway.mainnet.octopus.network",
    "moonriver.api.onfinality.io",
    "node-6957502816543653888.lh.onfinality.io",
    "node-7273232234617282560.nv.onfinality.io",
    "rpcnodea01.xode.net",
    "testrpcnodea01.xode.net",
    "spectrum-03.simplystaking.xyz",
)


def key_in(url: str) -> str | None:
    """Return the part of the URL that looks like a key, or None."""
    parsed = urlparse(url)

    for segment in parsed.path.split("/"):
        if KEY_LIKE_SEGMENT.match(segment):
            return segment

    for name, value in parse_qsl(parsed.query):
        if KEY_LIKE_QUERY_NAME.search(name) and not PLACEHOLDER.match(value):
            return value

    return None


def node_urls(config, chain_name="?"):
    """Yield (chain name, node URL) for every nodes list at any depth of the config."""
    if isinstance(config, dict):
        chain_name = config.get("name", chain_name) if "chainId" in config else chain_name

        for key, value in config.items():
            if key == "nodes" and isinstance(value, list):
                for node in value:
                    if isinstance(node, dict) and isinstance(node.get("url"), str):
                        yield chain_name, node["url"]
            else:
                yield from node_urls(value, chain_name)
    elif isinstance(config, list):
        for item in config:
            yield from node_urls(item, chain_name)


def redact(url: str, key: str) -> str:
    return url.replace(key, f"{key[:4]}...")


def check(path: Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []

    for chain_name, url in node_urls(json.loads(path.read_text(encoding="utf-8"))):
        key = key_in(url)
        if key is None:
            continue

        message = f"{path}: {chain_name}: node URL carries a key: {redact(url, key)}"

        if urlparse(url).hostname in KNOWN_KEYED_HOSTS:
            warnings.append(message)
        else:
            errors.append(message)

    return errors, warnings


def main(paths: list[str]) -> int:
    errors, warnings = [], []

    for path in paths:
        path_errors, path_warnings = check(Path(path))
        errors += path_errors
        warnings += path_warnings

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    if errors:
        print(
            "Use a keyless public node, or a placeholder such as {INFURA_API_KEY} for a key the apps own.",
            file=sys.stderr,
        )

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
