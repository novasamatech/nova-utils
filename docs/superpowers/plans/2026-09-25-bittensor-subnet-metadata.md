# Bittensor Subnet Metadata Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish `bittensor/v1/subnets.json` (netuid, name, symbol, logo) plus normalised 256 px PNG logos, refreshed daily by an auto-PR workflow.

**Architecture:** Three units in `scripts/bittensor/`: `chain_source.py` reads Subtensor storage via `substrate-interface`; `logo_normalizer.py` turns any downloaded logo into a deterministic 256×256 PNG; `update_subnets.py` downloads, merges with the previous snapshot (pure `merge()`), writes files. A scheduled GitHub workflow runs it and opens a PR.

**Tech Stack:** Python 3.10, substrate-interface 1.7.4, Pillow, cairosvg (needs system cairo), requests, pytest.

Spec: `docs/superpowers/specs/2026-09-25-bittensor-subnet-metadata-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `scripts/bittensor/__init__.py` | package marker |
| `scripts/bittensor/chain_source.py` | `Subnet`, `ChainSourceError`, `bittensor_node_urls()`, `subnets_from_storage()`, `fetch_subnets()` |
| `scripts/bittensor/logo_normalizer.py` | `LogoError`, `normalize(raw) -> png bytes` |
| `scripts/bittensor/update_subnets.py` | download, `merge()`, file I/O, CLI entry point |
| `tests/bittensor/__init__.py` | package marker |
| `tests/bittensor/test_chain_source.py` | storage → `Subnet` mapping |
| `tests/bittensor/test_logo_normalizer.py` | formats, aspect, determinism, rejects |
| `tests/bittensor/test_merge.py` | merge rules + abort guard |
| `tests/bittensor/test_subnets_snapshot.py` | committed JSON ↔ PNG files consistency |
| `.github/workflows/update_bittensor_subnets.yaml` | daily cron → auto-PR |
| `makefile` | `update-bittensor-subnets`, `test-bittensor` targets |
| `pyproject.toml`, `poetry.lock` | Pillow, cairosvg, requests |
| `CLAUDE.md` | note generated files + cairo requirement |
| `bittensor/v1/subnets.json`, `icons/bittensor/subnets/*.png` | first generated snapshot |

Run all Python from the repo root with `PYTHONPATH=.`.

---

### Task 1: Dependencies and make targets

**Files:** Modify `pyproject.toml`, `poetry.lock`, `makefile`

- [ ] **Step 1: Add dependencies**

Run: `.venv/bin/poetry add Pillow cairosvg requests` (fallback: `poetry add ...` if the venv has no poetry binary).
Expected: `pyproject.toml` gains three lines under `[tool.poetry.dependencies]`, `poetry.lock` updated, packages installed into `.venv`.

- [ ] **Step 2: Verify imports and cairo**

Run: `.venv/bin/python -c "import PIL, cairosvg, requests; print('ok')"`
Expected: `ok`. If `cairosvg` fails with `no library called "cairo"`, run `brew install cairo` (macOS).

- [ ] **Step 3: Add make targets** (append after the `update-chains-preconfigured` target)

```make
## Update Bittensor subnet metadata (names, symbols, logos) from chain
update-bittensor-subnets:
	$(PYTHON_SCRIPT) scripts/bittensor/update_subnets.py

## Run offline Bittensor subnet metadata tests
test-bittensor:
	PYTHONPATH=. $(VENV)/bin/python -m pytest tests/bittensor -v
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml poetry.lock makefile
git commit -m "build: add Pillow, cairosvg, requests and bittensor make targets"
```

---

### Task 2: chain_source

**Files:** Create `scripts/bittensor/__init__.py` (empty), `scripts/bittensor/chain_source.py`, `tests/bittensor/__init__.py` (empty), `tests/bittensor/test_chain_source.py`

- [ ] **Step 1: Write the failing test** — `tests/bittensor/test_chain_source.py`

```python
import json

import pytest

from scripts.bittensor.chain_source import (
    BITTENSOR_CHAIN_ID, ChainSourceError, Subnet, bittensor_node_urls, subnets_from_storage,
)


def test_maps_storage_to_subnets_sorted_by_netuid():
    added = {2: True, 0: True, 1: True}
    identities = {1: {"subnet_name": " Apex ", "logo_url": " https://x/logo.png "}}
    symbols = {0: "Τ", 1: "α", 2: "β"}

    assert subnets_from_storage(added, identities, symbols) == [
        Subnet(netuid=0, name=None, symbol="Τ", logo_url=None),
        Subnet(netuid=1, name="Apex", symbol="α", logo_url="https://x/logo.png"),
        Subnet(netuid=2, name=None, symbol="β", logo_url=None),
    ]


def test_skips_networks_not_added():
    assert subnets_from_storage({1: False, 2: True}, {}, {2: "β"}) == [
        Subnet(netuid=2, name=None, symbol="β", logo_url=None),
    ]


def test_empty_strings_become_none():
    identities = {3: {"subnet_name": "  ", "logo_url": ""}}
    assert subnets_from_storage({3: True}, identities, {3: "γ"}) == [
        Subnet(netuid=3, name=None, symbol="γ", logo_url=None),
    ]


def test_hex_encoded_bytes_are_decoded():
    identities = {4: {"subnet_name": "0x" + "Chutes".encode().hex(), "logo_url": None}}
    assert subnets_from_storage({4: True}, identities, {4: "0x" + "ش".encode().hex()}) == [
        Subnet(netuid=4, name="Chutes", symbol="ش", logo_url=None),
    ]


def test_node_urls_read_from_chains_file(tmp_path):
    chains = [
        {"chainId": "other", "nodes": [{"url": "wss://other"}]},
        {"chainId": BITTENSOR_CHAIN_ID, "nodes": [{"url": "wss://a"}, {"url": "wss://b"}]},
    ]
    path = tmp_path / "chains.json"
    path.write_text(json.dumps(chains))

    assert bittensor_node_urls(str(path)) == ["wss://a", "wss://b"]


def test_node_urls_missing_chain_raises(tmp_path):
    path = tmp_path / "chains.json"
    path.write_text("[]")

    with pytest.raises(ChainSourceError):
        bittensor_node_urls(str(path))
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=. .venv/bin/python -m pytest tests/bittensor/test_chain_source.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.bittensor'`

- [ ] **Step 3: Implement** — `scripts/bittensor/chain_source.py`

```python
import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from substrateinterface import SubstrateInterface

from scripts.utils.chain_model import Chain

BITTENSOR_CHAIN_ID = "2f0555cc76fc2840a25a6ea3b9637146806f1f44b090c175ffde2a7e5ab36c03"
PALLET = "SubtensorModule"


@dataclass(frozen=True)
class Subnet:
    netuid: int
    name: Optional[str]
    symbol: str
    logo_url: Optional[str]


class ChainSourceError(Exception):
    pass


def bittensor_node_urls(chains_path: Optional[str] = None) -> List[str]:
    path = chains_path or f"chains/{Chain.latest_config_version()}/chains.json"
    with open(path, encoding="utf-8") as f:
        chains = json.load(f)
    for chain in chains:
        if chain["chainId"] == BITTENSOR_CHAIN_ID:
            return [node["url"] for node in chain["nodes"]]
    raise ChainSourceError(f"Bittensor chain not found in {path}")


def _text(value) -> Optional[str]:
    """Vec<u8> fields decode as str when valid UTF-8; fall back to decoding a hex string."""
    if not value:
        return None
    if value.startswith("0x"):
        try:
            value = bytes.fromhex(value[2:]).decode("utf-8")
        except ValueError:
            pass
    return value.strip() or None


def subnets_from_storage(
    networks_added: Dict[int, bool],
    identities: Dict[int, dict],
    symbols: Dict[int, str],
) -> List[Subnet]:
    subnets = []
    for netuid in sorted(n for n, added in networks_added.items() if added):
        identity = identities.get(netuid) or {}
        subnets.append(Subnet(
            netuid=netuid,
            name=_text(identity.get("subnet_name")),
            symbol=_text(symbols.get(netuid)) or "",
            logo_url=_text(identity.get("logo_url")),
        ))
    return subnets


def _query_map(substrate: SubstrateInterface, storage: str) -> dict:
    return {int(key.value): value.value for key, value in substrate.query_map(PALLET, storage, page_size=1000)}


def fetch_subnets(node_urls: List[str]) -> List[Subnet]:
    errors = []
    for url in node_urls:
        substrate = None
        try:
            substrate = SubstrateInterface(url=url)
            return subnets_from_storage(
                _query_map(substrate, "NetworksAdded"),
                _query_map(substrate, "SubnetIdentitiesV3"),
                _query_map(substrate, "TokenSymbol"),
            )
        except Exception as e:
            errors.append(f"{url}: {e!r}")
        finally:
            if substrate is not None:
                substrate.close()
    raise ChainSourceError("No Bittensor node answered: " + "; ".join(errors))
```

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONPATH=. .venv/bin/python -m pytest tests/bittensor/test_chain_source.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/bittensor/__init__.py scripts/bittensor/chain_source.py tests/bittensor/__init__.py tests/bittensor/test_chain_source.py
git commit -m "feat: read Bittensor subnet identities and symbols from storage"
```

---

### Task 3: logo_normalizer

**Files:** Create `scripts/bittensor/logo_normalizer.py`, `tests/bittensor/test_logo_normalizer.py`

- [ ] **Step 1: Write the failing test** — `tests/bittensor/test_logo_normalizer.py`

```python
import io

import pytest
from PIL import Image

from scripts.bittensor.logo_normalizer import SIZE, LogoError, normalize


def encode(img: Image.Image, fmt: str) -> bytes:
    out = io.BytesIO()
    img.save(out, fmt)
    return out.getvalue()


def decode(png: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(png))
    assert img.format == "PNG"
    return img


@pytest.mark.parametrize("fmt, mode", [("PNG", "RGBA"), ("JPEG", "RGB"), ("WEBP", "RGBA"), ("GIF", "P")])
def test_raster_formats_become_256_rgba_png(fmt, mode):
    img = decode(normalize(encode(Image.new(mode, (40, 40)), fmt)))
    assert img.size == (SIZE, SIZE)
    assert img.mode == "RGBA"


def test_ico_uses_largest_frame():
    source = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
    img = decode(normalize(encode(source, "ICO")))
    assert img.size == (SIZE, SIZE)
    assert img.getpixel((SIZE // 2, SIZE // 2)) == (255, 0, 0, 255)


def test_svg_is_rasterised():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="#00ff00"/></svg>'
    img = decode(normalize(svg))
    assert img.size == (SIZE, SIZE)
    assert img.getpixel((SIZE // 2, SIZE // 2)) == (0, 255, 0, 255)


def test_svg_with_xml_prolog_is_rasterised():
    svg = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4"/></svg>'
    assert decode(normalize(svg)).size == (SIZE, SIZE)


def test_non_square_keeps_aspect_with_transparent_padding():
    wide = Image.new("RGBA", (200, 100), (0, 0, 255, 255))
    img = decode(normalize(encode(wide, "PNG")))
    assert img.getpixel((SIZE // 2, 5)) == (0, 0, 0, 0)
    assert img.getpixel((SIZE // 2, SIZE // 2)) == (0, 0, 255, 255)
    assert img.getpixel((2, SIZE // 2)) == (0, 0, 255, 255)


def test_output_is_deterministic():
    raw = encode(Image.new("RGB", (33, 17), (10, 20, 30)), "JPEG")
    assert normalize(raw) == normalize(raw)


@pytest.mark.parametrize("raw", [
    b"<!DOCTYPE html><html><body><svg></svg></body></html>",
    b"<html><head></head></html>",
    b"not an image at all",
    b"",
])
def test_rejects_non_images(raw):
    with pytest.raises(LogoError):
        normalize(raw)


def test_svg_external_references_are_not_fetched():
    svg = (b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="4" height="4">'
           b'<image xlink:href="http://127.0.0.1:9/x.png" width="4" height="4"/></svg>')
    assert decode(normalize(svg)).size == (SIZE, SIZE)
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=. .venv/bin/python -m pytest tests/bittensor/test_logo_normalizer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.bittensor.logo_normalizer'`

- [ ] **Step 3: Implement** — `scripts/bittensor/logo_normalizer.py`

```python
import io

import cairosvg
from cairosvg.url import fetch as cairosvg_fetch
from PIL import Image

SIZE = 256
_SVG_PROLOGS = (b"<svg", b"<?xml", b"<!--")


class LogoError(Exception):
    pass


def _is_svg(raw: bytes) -> bool:
    head = raw[:4096].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    return head.startswith(_SVG_PROLOGS) and b"<svg" in head and b"<html" not in head


def _data_urls_only(url, resource_type):
    # Untrusted SVGs must not make the job fetch arbitrary URLs or local files.
    if url.startswith("data:"):
        return cairosvg_fetch(url, resource_type)
    raise LogoError(f"external reference blocked: {url}")


def _open_svg(raw: bytes) -> Image.Image:
    def render(**kwargs) -> Image.Image:
        png = cairosvg.svg2png(bytestring=raw, url_fetcher=_data_urls_only, **kwargs)
        return Image.open(io.BytesIO(png))

    try:
        natural = render()
        # Re-render at the target size instead of upscaling a tiny bitmap.
        return render(scale=SIZE / max(natural.size))
    except LogoError:
        raise
    except Exception as e:
        raise LogoError(f"cannot render SVG: {e!r}") from e


def _open_raster(raw: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
        return img
    except Exception as e:
        raise LogoError(f"cannot decode image: {e!r}") from e


def _fit(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    scale = SIZE / max(img.size)
    width, height = max(1, round(img.width * scale)), max(1, round(img.height * scale))
    img = img.resize((width, height), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, ((SIZE - width) // 2, (SIZE - height) // 2))
    return canvas


def normalize(raw: bytes) -> bytes:
    """Return a SIZE×SIZE RGBA PNG for any supported logo, or raise LogoError."""
    img = _open_svg(raw) if _is_svg(raw) else _open_raster(raw)
    out = io.BytesIO()
    _fit(img).save(out, "PNG", compress_level=9)
    return out.getvalue()
```

Note on `test_svg_external_references_are_not_fetched`: if cairosvg propagates the fetcher error for `<image>` instead of skipping the element, change the test to `pytest.raises(LogoError)` — either outcome satisfies "nothing is fetched"; what matters is no network access and a clean `LogoError` or a rendered PNG.

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONPATH=. .venv/bin/python -m pytest tests/bittensor/test_logo_normalizer.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add scripts/bittensor/logo_normalizer.py tests/bittensor/test_logo_normalizer.py
git commit -m "feat: normalise subnet logos to deterministic 256px PNG"
```

---

### Task 4: merge and update_subnets entry point

**Files:** Create `scripts/bittensor/update_subnets.py`, `tests/bittensor/test_merge.py`

- [ ] **Step 1: Write the failing test** — `tests/bittensor/test_merge.py`

```python
import pytest

from scripts.bittensor.chain_source import Subnet
from scripts.bittensor.update_subnets import UpdateAborted, logo_filename, logo_url, merge

PNG_A = b"png-a"
PNG_B = b"png-b"


def subnet(netuid, logo_url_=None, name="Name", symbol="α"):
    return Subnet(netuid=netuid, name=name, symbol=symbol, logo_url=logo_url_)


def entry(netuid, logo, name="Name", symbol="α"):
    return {"netuid": netuid, "name": name, "symbol": symbol, "logo": logo}


def test_new_logo_is_written_and_referenced():
    result = merge([], [subnet(1, "https://x/a.png")], {1: PNG_A}, [])
    filename = logo_filename(1, PNG_A)
    assert result.entries == [entry(1, logo_url(filename))]
    assert result.files_to_write == {filename: PNG_A}
    assert result.files_to_delete == []


def test_unchanged_logo_writes_and_deletes_nothing():
    filename = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(filename))], [subnet(1, "https://x/a.png")], {1: PNG_A}, [filename])
    assert result.files_to_write == {}
    assert result.files_to_delete == []


def test_changed_logo_replaces_old_file():
    old, new = logo_filename(1, PNG_A), logo_filename(1, PNG_B)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: PNG_B}, [old])
    assert result.entries == [entry(1, logo_url(new))]
    assert result.files_to_write == {new: PNG_B}
    assert result.files_to_delete == [old]


def test_failed_download_keeps_previous_logo():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: "HTTPError: 404"}, [old])
    assert result.entries == [entry(1, logo_url(old))]
    assert result.files_to_delete == []
    assert result.kept_previous == {1: "HTTPError: 404"}


def test_failed_download_without_previous_gives_null():
    result = merge([], [subnet(1, "https://x/a.png")], {1: "LogoError: html"}, [])
    assert result.entries == [entry(1, None)]
    assert result.missing == {1: "LogoError: html"}


def test_previous_logo_whose_file_is_gone_is_not_kept():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, "https://x/a.png")], {1: "timeout"}, [])
    assert result.entries == [entry(1, None)]


def test_logo_removed_on_chain_gives_null_and_deletes_file():
    old = logo_filename(1, PNG_A)
    result = merge([entry(1, logo_url(old))], [subnet(1, None)], {}, [old])
    assert result.entries == [entry(1, None)]
    assert result.files_to_delete == [old]
    assert result.missing == {}


def test_entries_sorted_and_carry_name_and_symbol():
    result = merge([], [subnet(2, name=None, symbol="β"), subnet(0, symbol="Τ")], {}, [])
    assert result.entries == [entry(0, None, symbol="Τ"), entry(2, None, name=None, symbol="β")]


def test_aborts_when_chain_returns_less_than_half():
    previous = [entry(n, None) for n in range(10)]
    with pytest.raises(UpdateAborted):
        merge(previous, [subnet(n) for n in range(4)], {}, [])


def test_half_is_accepted():
    previous = [entry(n, None) for n in range(10)]
    assert len(merge(previous, [subnet(n) for n in range(5)], {}, []).entries) == 5
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=. .venv/bin/python -m pytest tests/bittensor/test_merge.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.bittensor.update_subnets'`

- [ ] **Step 3: Implement** — `scripts/bittensor/update_subnets.py`

```python
"""Regenerate bittensor/v1/subnets.json and icons/bittensor/subnets/ from Bittensor chain state.

Run from the repo root: `make update-bittensor-subnets`.
"""
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

import requests

from scripts.bittensor.chain_source import ChainSourceError, Subnet, bittensor_node_urls, fetch_subnets
from scripts.bittensor.logo_normalizer import LogoError, normalize

SUBNETS_JSON = "bittensor/v1/subnets.json"
LOGO_DIR = "icons/bittensor/subnets"
LOGO_BASE_URL = f"https://raw.githubusercontent.com/novasamatech/nova-utils/master/{LOGO_DIR}"
DOWNLOAD_TIMEOUT = 15
MAX_LOGO_BYTES = 5 * 1024 * 1024
DOWNLOAD_WORKERS = 16
USER_AGENT = "Mozilla/5.0 (compatible; nova-utils-subnet-metadata)"

# Per netuid: normalised PNG bytes on success, a human-readable reason on failure.
LogoOutcome = Union[bytes, str]


class UpdateAborted(Exception):
    pass


@dataclass
class MergeResult:
    entries: List[dict]
    files_to_write: Dict[str, bytes]
    files_to_delete: List[str]
    kept_previous: Dict[int, str] = field(default_factory=dict)
    missing: Dict[int, str] = field(default_factory=dict)


def logo_filename(netuid: int, png: bytes) -> str:
    return f"sn{netuid}-{hashlib.sha256(png).hexdigest()[:8]}.png"


def logo_url(filename: str) -> str:
    return f"{LOGO_BASE_URL}/{filename}"


def _filename(url: str) -> str:
    return url.rsplit("/", 1)[-1]


def merge(
    previous: List[dict],
    subnets: List[Subnet],
    logos: Dict[int, LogoOutcome],
    existing_files: List[str],
) -> MergeResult:
    if previous and len(subnets) < len(previous) / 2:
        raise UpdateAborted(f"chain returned {len(subnets)} subnets, current file has {len(previous)}")

    previous_logo = {
        e["netuid"]: e["logo"] for e in previous
        if e.get("logo") and _filename(e["logo"]) in existing_files
    }
    result = MergeResult(entries=[], files_to_write={}, files_to_delete=[])

    for subnet in sorted(subnets, key=lambda s: s.netuid):
        outcome = logos.get(subnet.netuid)
        logo: Optional[str] = None
        if isinstance(outcome, bytes):
            filename = logo_filename(subnet.netuid, outcome)
            logo = logo_url(filename)
            if filename not in existing_files:
                result.files_to_write[filename] = outcome
        elif subnet.logo_url and subnet.netuid in previous_logo:
            logo = previous_logo[subnet.netuid]
            result.kept_previous[subnet.netuid] = outcome
        elif subnet.logo_url:
            result.missing[subnet.netuid] = outcome

        result.entries.append({"netuid": subnet.netuid, "name": subnet.name, "symbol": subnet.symbol, "logo": logo})

    referenced = {_filename(e["logo"]) for e in result.entries if e["logo"]}
    result.files_to_delete = sorted(f for f in existing_files if f not in referenced)
    return result


def download(url: str) -> bytes:
    with requests.get(url, timeout=DOWNLOAD_TIMEOUT, headers={"User-Agent": USER_AGENT}, stream=True) as response:
        response.raise_for_status()
        chunks, size = [], 0
        for chunk in response.iter_content(64 * 1024):
            size += len(chunk)
            if size > MAX_LOGO_BYTES:
                raise LogoError(f"larger than {MAX_LOGO_BYTES} bytes")
            chunks.append(chunk)
    return b"".join(chunks)


def fetch_logo(subnet: Subnet) -> LogoOutcome:
    try:
        return normalize(download(subnet.logo_url))
    except (requests.RequestException, LogoError) as e:
        return f"{type(e).__name__}: {e}"


def load_previous(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)["subnets"]


def write_subnets_json(path: str, entries: List[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"subnets": entries}, f, indent=2, ensure_ascii=False)
        f.write("\n")


def existing_logo_files(directory: str) -> List[str]:
    if not os.path.isdir(directory):
        return []
    return sorted(f for f in os.listdir(directory) if f.endswith(".png"))


def main() -> None:
    previous = load_previous(SUBNETS_JSON)
    subnets = fetch_subnets(bittensor_node_urls())

    with_logo = [s for s in subnets if s.logo_url]
    with ThreadPoolExecutor(DOWNLOAD_WORKERS) as pool:
        logos = dict(zip((s.netuid for s in with_logo), pool.map(fetch_logo, with_logo)))

    result = merge(previous, subnets, logos, existing_logo_files(LOGO_DIR))

    os.makedirs(LOGO_DIR, exist_ok=True)
    for filename, png in result.files_to_write.items():
        with open(os.path.join(LOGO_DIR, filename), "wb") as f:
            f.write(png)
    for filename in result.files_to_delete:
        os.remove(os.path.join(LOGO_DIR, filename))
    write_subnets_json(SUBNETS_JSON, result.entries)

    with_logos = sum(1 for e in result.entries if e["logo"])
    print(f"{len(result.entries)} subnets, {with_logos} with logo; "
          f"{len(result.files_to_write)} logos written, {len(result.files_to_delete)} deleted")
    for title, failures in (("Kept previous logo", result.kept_previous), ("No logo", result.missing)):
        for netuid, reason in sorted(failures.items()):
            print(f"  {title} for SN{netuid}: {reason}")


if __name__ == "__main__":
    try:
        main()
    except (ChainSourceError, UpdateAborted) as e:
        print(f"Aborted: {e}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONPATH=. .venv/bin/python -m pytest tests/bittensor -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add scripts/bittensor/update_subnets.py tests/bittensor/test_merge.py
git commit -m "feat: generate Bittensor subnets.json with previous-logo fallback"
```

---

### Task 5: First snapshot + consistency test

**Files:** Create `bittensor/v1/subnets.json`, `icons/bittensor/subnets/*.png` (generated), `tests/bittensor/test_subnets_snapshot.py`

- [ ] **Step 1: Generate**

Run: `make update-bittensor-subnets`
Expected: a summary like `129 subnets, ~84 with logo; ~84 logos written, 0 deleted` followed by `No logo for SN..` lines for broken sources.

- [ ] **Step 2: Re-run to confirm idempotence**

Run: `make update-bittensor-subnets && git status --porcelain bittensor icons/bittensor`
Expected: `0 logos written, 0 deleted`; git status shows only the untracked directories from step 1 (no content changes between runs). If some logo host returns different bytes per request, note it in the PR — the hash will churn only for that subnet.

- [ ] **Step 3: Spot-check output**

Open 3–4 PNGs (e.g. SN1, SN64, one former SVG) and verify they look right; read `subnets.json` head.

- [ ] **Step 4: Write the consistency test** — `tests/bittensor/test_subnets_snapshot.py`

```python
import json
import os

from scripts.bittensor.update_subnets import LOGO_BASE_URL, LOGO_DIR, SUBNETS_JSON, existing_logo_files


def load_entries():
    with open(SUBNETS_JSON, encoding="utf-8") as f:
        return json.load(f)["subnets"]


def test_entries_are_sorted_and_unique():
    netuids = [e["netuid"] for e in load_entries()]
    assert netuids == sorted(set(netuids))


def test_every_logo_points_to_existing_file():
    for e in load_entries():
        if e["logo"]:
            assert e["logo"].startswith(LOGO_BASE_URL + "/"), e
            assert os.path.isfile(os.path.join(LOGO_DIR, e["logo"].rsplit("/", 1)[-1])), e


def test_no_unreferenced_logo_files():
    referenced = {e["logo"].rsplit("/", 1)[-1] for e in load_entries() if e["logo"]}
    assert set(existing_logo_files(LOGO_DIR)) == referenced
```

- [ ] **Step 5: Run all bittensor tests**

Run: `make test-bittensor`
Expected: all passed

- [ ] **Step 6: Commit**

```bash
git add bittensor icons/bittensor tests/bittensor/test_subnets_snapshot.py
git commit -m "feat: add first Bittensor subnet metadata snapshot"
```

---

### Task 6: Daily workflow

**Files:** Create `.github/workflows/update_bittensor_subnets.yaml`

- [ ] **Step 1: Write the workflow**

```yaml
name: Update Bittensor subnet metadata

on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  update-subnets:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout current repository to Master branch
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: 🛠 Set up actual paths
        uses: ./.github/workflows/setup-path

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install cairo for SVG logos
        run: sudo apt-get update && sudo apt-get install -y libcairo2

      - name: ⚙️ Install dependencies
        run: make init

      - name: 🦾 Update subnet names, symbols and logos
        run: make update-bittensor-subnets

      - name: Make Pull Request
        uses: ./.github/workflows/make-pull-request
        with:
          commit-files: |
            bittensor/**
            icons/bittensor/**
          commit-message: Update Bittensor subnet metadata
          app-id: ${{ secrets.PR_APP_ID}}
          app-token: ${{ secrets.PR_APP_TOKEN}}
          pr-reviewer: ${{ env.PR_REVIEWER }}
          branch-name: update-bittensor-subnets
          pr-title: 🆙 Update Bittensor subnet metadata
          pr-body: This PR was generated automatically 🤖
          pr-base: master

  alert:
    runs-on: ubuntu-latest
    needs: update-subnets
    if: always() && (needs.update-subnets.result == 'failure')
    env:
      GITHUB_WORKFLOW_URL: https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}
    steps:
      - name: Report
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_TO }}
          token: ${{ secrets.TELEGRAM_TOKEN }}
          message: |
            Bittensor subnet metadata update failed, lets check:

            Failed run:
            ${{ env.GITHUB_WORKFLOW_URL }}
```

- [ ] **Step 2: Validate YAML**

Run: `.venv/bin/python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/update_bittensor_subnets.yaml')); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/update_bittensor_subnets.yaml
git commit -m "ci: refresh Bittensor subnet metadata daily via auto-PR"
```

---

### Task 7: Docs, checks, PR

**Files:** Modify `CLAUDE.md`

- [ ] **Step 1: Document generated files** — in `CLAUDE.md` under "Generated files — never edit by hand", add:

```markdown
- `bittensor/v1/subnets.json` + `icons/bittensor/subnets/*.png` ← `make update-bittensor-subnets` (daily workflow opens a PR; SVG logos need the system cairo library — `brew install cairo` locally)
```

- [ ] **Step 2: Run checks**

Run: `.venv/bin/pre-commit run --files $(git diff --name-only novasamatech/master...HEAD) CLAUDE.md` and `make test-bittensor`
Expected: all hooks Passed/Skipped; tests pass.

- [ ] **Step 3: Commit, push, open PR**

```bash
git add CLAUDE.md
git commit -m "docs: note generated Bittensor subnet metadata"
git push -u novasamatech feat/bittensor-subnet-metadata
gh pr create --repo novasamatech/nova-utils --base master --title "feat: Bittensor subnet metadata (NW-2191)" --body-file <body>
```
