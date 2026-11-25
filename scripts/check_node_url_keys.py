"""Check that no node URL in a chains config carries a provider key.

This repository is public and the clients read it as is, so a key written into a node URL is a
leaked key: anyone can spend its quota. A key that the apps own is written as a placeholder such
as {INFURA_API_KEY}; the apps substitute their built-in value when they open the connection.

The check fails closed: every part of a node URL is inspected (user info, host labels, path
segments, query values and fragment), and anything that looks like a credential is an error
unless that exact URL is in the baseline of URLs that were in the configs before the check.

Run over one or more chains config paths:

    python3 scripts/check_node_url_keys.py chains/v23/chains.json
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

BASELINE_PATH = Path(__file__).with_name("known_keyed_node_urls.txt")

# The shortest keyed segment found in the configs is 15 characters (Zeeve endpoints); the longest
# legitimate mixed segment is far shorter ("v3", "public-ws", "ogws").
MIN_KEY_LENGTH = 12
# A segment of one character class (all letters, all digits) is a key only when it is long:
# shorter ones are words and numbers, such as chain names and port-like ids.
MIN_SINGLE_CLASS_KEY_LENGTH = 24
# Host names legitimately mix letters and digits ("testrpcnodea01"), so only a long run counts.
MIN_HOST_KEY_LENGTH = 20
REDACTED_PREFIX_LENGTH = 4

KEY_CHARACTERS = re.compile(r"^[A-Za-z0-9_\-+=.~]+$")
# A query parameter with one of these names carries a credential whatever its value looks like.
KEY_LIKE_QUERY_NAME = re.compile(
    r"key$|token|secret|auth|jwt|password|passwd|project[_-]?id|^access", re.IGNORECASE
)
PLACEHOLDER = re.compile(r"^\{[A-Z0-9_]+\}$")
# The placeholders both apps can substitute; any other one leaves the node unusable.
KNOWN_PLACEHOLDERS = frozenset({"{INFURA_API_KEY}", "{DWELLIR_API_KEY}"})


def looks_like_key(value: str) -> bool:
    """A long run of key characters: mixed letters and digits, or very long of one class."""
    if not KEY_CHARACTERS.match(value):
        return False

    compact = re.sub(r"[^A-Za-z0-9]", "", value)
    is_mixed = bool(re.search(r"\d", compact)) and bool(re.search(r"[A-Za-z]", compact))

    if is_mixed:
        return len(compact) >= MIN_KEY_LENGTH

    return len(compact) >= MIN_SINGLE_CLASS_KEY_LENGTH


def host_label_key(label: str) -> str | None:
    """Host labels are hyphenated words ("xode-polkadot-rpc-01"), so each word is judged alone."""
    for word in label.split("-"):
        if len(word) >= MIN_HOST_KEY_LENGTH and looks_like_key(word):
            return word

    return None


def problem_in(url: str) -> tuple[str, str] | None:
    """Return (what is wrong, the offending part of the URL), or None for a clean URL."""
    if url != url.strip():
        return "surrounding whitespace", url

    parts = urlsplit(url)

    if parts.username or parts.password:
        return "user info", url.split("://", 1)[-1].split("@", 1)[0]

    for label in (parts.hostname or "").split("."):
        key = host_label_key(label)
        if key:
            return "a key in the host", key

    for raw_segment in parts.path.split("/"):
        segment = unquote(raw_segment)

        if "{" in segment or "}" in segment:
            if segment not in KNOWN_PLACEHOLDERS:
                return "an unknown or malformed placeholder", raw_segment
            continue

        # ";" separates matrix parameters, which carry keys as well as the segment itself
        for piece in re.split(r"[;,]", segment):
            if looks_like_key(piece):
                return "a key in the path", raw_segment if piece == segment else piece

    for name, value in parse_qsl(parts.query, keep_blank_values=True):
        if PLACEHOLDER.match(value):
            if value not in KNOWN_PLACEHOLDERS:
                return "an unknown placeholder", value
            continue

        if value and (KEY_LIKE_QUERY_NAME.search(name) or looks_like_key(value)):
            return f"a key in the query parameter '{name}'", value

    if parts.fragment and looks_like_key(parts.fragment):
        return "a key in the fragment", parts.fragment

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


def fingerprint(url: str) -> str:
    """The baseline stores hashes, so that it does not repeat the keys in one more file."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def load_baseline(path: Path = BASELINE_PATH) -> frozenset[str]:
    """Fingerprints of the keyed URLs that predate the check; lines starting with # are comments."""
    lines = path.read_text(encoding="utf-8").splitlines()

    return frozenset(line.split()[0] for line in lines if line.strip() and not line.startswith("#"))


def redact(url: str, part: str) -> str:
    """Show where the key is without printing it: the host and the first characters of the key."""
    host = urlsplit(url).hostname or "?"

    return f"{host}: {part[:REDACTED_PREFIX_LENGTH]}..."


def check(path: Path, baseline: frozenset[str]) -> tuple[list[str], dict[str, str]]:
    """Return the errors of one file and its baseline URLs as {fingerprint: redacted message}."""
    errors, known = [], {}

    for chain_name, url in node_urls(json.loads(path.read_text(encoding="utf-8"))):
        problem = problem_in(url)
        if problem is None:
            continue

        reason, part = problem
        message = f"{chain_name}: node URL has {reason} ({redact(url, part)})"

        if fingerprint(url) in baseline:
            known.setdefault(fingerprint(url), message)
        else:
            errors.append(f"{path}: {message}")

    return errors, known


def main(paths: list[str]) -> int:
    """Print every error, and each baseline URL once however many files repeat it."""
    baseline = load_baseline()
    errors, known = [], {}

    for path in paths:
        path_errors, path_known = check(Path(path), baseline)
        errors += path_errors
        known.update(path_known)

    for message in sorted(known.values()):
        print(f"warning: known keyed URL, still to be removed: {message}", file=sys.stderr)

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
