"""Check that no node URL in a chains config carries a provider key.

This repository is public and the clients read it as is, so a key written into a node URL is a
leaked key: anyone can spend its quota. A key that the apps own is written as a placeholder such
as {INFURA_API_KEY}; the apps substitute their built-in value when they open the connection.

Every part of a node URL is inspected (user info, host labels, path segments, query names and
values, fragment). Anything that looks like a credential is an error unless that exact URL is in
the baseline of keyed URLs that were in the configs before the check. The check is a heuristic:
it is strict on purpose and can reject a harmless URL; such a URL goes into the reviewed list of
false positives, never into the baseline.

Run over one or more chains config paths:

    python3 scripts/check_node_url_keys.py chains/v23/chains.json
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

BASELINE_PATH = Path(__file__).with_name("known_keyed_node_urls.txt")
FALSE_POSITIVES_PATH = Path(__file__).with_name("node_url_false_positives.txt")

# Measured over the configs: the longest harmless run that mixes letters and digits has 10 of
# them ("zksync2-era"); the shortest keyed one has 15 (Zeeve endpoints). 12 leaves little room on
# the harmless side, so re-measure before lowering it.
MIN_KEY_LENGTH = 12
# A run of one character class (all letters, all digits) is a key only when it is long: shorter
# ones are words and numbers, such as chain names and node ids.
MIN_SINGLE_CLASS_KEY_LENGTH = 24
# Host names legitimately mix letters and digits ("testrpcnodea01"), so only a long run counts.
MIN_HOST_KEY_LENGTH = 20
REDACTED_PREFIX_LENGTH = 4

KEY_CHARACTER_RUN = re.compile(r"[A-Za-z0-9_\-+=.~]+")
# A host label that is one long hexadecimal value once its hyphens are dropped, such as a UUID.
HEX_HOST_LABEL = re.compile(r"^[0-9a-f]{%d,}$" % MIN_SINGLE_CLASS_KEY_LENGTH, re.IGNORECASE)
# A query parameter with one of these names carries a credential whatever its value looks like.
KEY_LIKE_QUERY_NAME = re.compile(
    r"key$|token|secret|auth|jwt|password|passwd|project[_-]?id|^access", re.IGNORECASE
)
# The placeholders both apps can substitute, and the hosts each may be sent to: the apps put
# their built-in key into any URL that names it, so a foreign host would simply receive the key.
PLACEHOLDER_HOST_SUFFIXES = {
    "{INFURA_API_KEY}": ".infura.io",
    "{DWELLIR_API_KEY}": ".dwellir.com",
}
BRACE = re.compile(r"[{}]|%7b|%7d", re.IGNORECASE)


def looks_like_key(run: str) -> bool:
    """Judge one run of key characters: mixed letters and digits, or very long of one class."""
    compact = re.sub(r"[^A-Za-z0-9]", "", run)
    is_mixed = bool(re.search(r"\d", compact)) and bool(re.search(r"[A-Za-z]", compact))

    if is_mixed:
        return len(compact) >= MIN_KEY_LENGTH

    return len(compact) >= MIN_SINGLE_CLASS_KEY_LENGTH


def key_in(text: str) -> str | None:
    """Return the first run of key characters in the text that looks like a key."""
    for run in KEY_CHARACTER_RUN.findall(unquote(text)):
        if looks_like_key(run):
            return run

    return None


def host_key(hostname: str) -> str | None:
    """Host labels are hyphenated words ("xode-polkadot-rpc-01"), so each word is judged alone."""
    for label in hostname.split("."):
        if HEX_HOST_LABEL.match(label.replace("-", "")):
            return label

        for word in label.split("-"):
            if len(word) >= MIN_HOST_KEY_LENGTH and looks_like_key(word):
                return word

    return None


def placeholder_problem(url: str) -> tuple[str, str] | None:
    """Only known placeholders, written exactly, and only on the host of their provider."""
    hostname = urlsplit(url).hostname or ""
    remainder = url

    for placeholder, host_suffix in PLACEHOLDER_HOST_SUFFIXES.items():
        if placeholder not in url:
            continue

        if not hostname.endswith(host_suffix):
            return f"{placeholder} on a host that is not *{host_suffix}", placeholder

        remainder = remainder.replace(placeholder, "")

    brace = BRACE.search(remainder)
    if brace:
        return "an unknown or malformed placeholder", remainder[brace.start():brace.start() + 24]

    return None


def without_placeholders(url: str) -> str:
    for placeholder in PLACEHOLDER_HOST_SUFFIXES:
        url = url.replace(placeholder, "")

    return url


def problem_in(url: str) -> tuple[str, str] | None:
    """Return (what is wrong, the offending part of the URL), or None for a clean URL."""
    if url != url.strip():
        return "surrounding whitespace", url

    problem = placeholder_problem(url)
    if problem:
        return problem

    parts = urlsplit(without_placeholders(url))

    if parts.username or parts.password:
        return "user info", parts.netloc.rsplit("@", 1)[0]

    key = host_key(parts.hostname or "")
    if key:
        return "a key in the host", key

    for segment in parts.path.split("/"):
        key = key_in(segment)
        if key:
            return "a key in the path", key

    # Split by hand: parse_qsl turns "+" into a space and drops what has no "=".
    for pair in re.split(r"[&;]", parts.query):
        name, _, value = pair.partition("=")

        key = key_in(name)
        if key:
            return "a key in the query", key

        if value and KEY_LIKE_QUERY_NAME.search(unquote(name)):
            return f"a key in the query parameter '{unquote(name)}'", unquote(value)

        key = key_in(value)
        if key:
            return f"a key in the query parameter '{unquote(name)}'", key

    key = key_in(parts.fragment)
    if key:
        return "a key in the fragment", key

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


def first_tokens(path: Path) -> frozenset[str]:
    """The first word of every line that is not empty or a # comment."""
    lines = path.read_text(encoding="utf-8").splitlines()

    return frozenset(line.split()[0] for line in lines if line.strip() and not line.startswith("#"))


def load_baseline(path: Path = BASELINE_PATH) -> frozenset[str]:
    """Fingerprints of the keyed URLs that predate the check."""
    return first_tokens(path)


def load_false_positives(path: Path = FALSE_POSITIVES_PATH) -> frozenset[str]:
    """Harmless URLs the heuristic rejects, written in full so that a reviewer can read them."""
    return first_tokens(path)


def redact(url: str, part: str) -> str:
    """Show where the key is without printing it: the host and the first characters of the key."""
    host = urlsplit(without_placeholders(url)).hostname or "?"

    return f"{host}: {part[:REDACTED_PREFIX_LENGTH]}..."


def check(
    path: Path, baseline: frozenset[str], false_positives: frozenset[str] = frozenset()
) -> tuple[list[str], dict[str, str]]:
    """Return the errors of one file and its baseline URLs as {fingerprint: redacted message}."""
    errors, known = [], {}

    for chain_name, url in node_urls(json.loads(path.read_text(encoding="utf-8"))):
        problem = None if url in false_positives else problem_in(url)
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
    """Print every error, and each baseline URL once per run however many files repeat it."""
    baseline, false_positives = load_baseline(), load_false_positives()
    errors, known = [], {}

    for path in paths:
        path_errors, path_known = check(Path(path), baseline, false_positives)
        errors += path_errors
        known.update(path_known)

    for message in sorted(known.values()):
        print(f"warning: known keyed URL, still to be removed: {message}", file=sys.stderr)

    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    if errors:
        print(
            "Use a keyless public node, or a placeholder such as {INFURA_API_KEY} for a key the apps own.\n"
            "A harmless URL rejected by mistake goes into scripts/node_url_false_positives.txt.",
            file=sys.stderr,
        )

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
