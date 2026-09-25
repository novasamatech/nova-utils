# Bittensor subnet metadata — design

Jira: [NW-2191](https://novasama-technologies.atlassian.net/browse/NW-2191)

## Goal

Give Nova Wallet clients the name, token symbol and logo of every Bittensor subnet, refreshed daily without an app
release, with logos served from nova-utils rather than hot-linked from third-party hosts.

Acceptance (from the ticket):

- Subnet rows/cards show on-chain name, symbol and logo; identicon only when there is no logo.
- Metadata refreshes without an app release.
- Logos are served from our infrastructure.

## Scope

In scope: subnet metadata (`netuid`, `name`, `symbol`, `logo`), the generator script, a daily workflow, offline tests,
and the first generated snapshot.

Out of scope:

- Validator identities (`SubtensorModule.IdentitiesV2`) for the validator picker — follow-up task.
- App-side changes (bittensor API response, identicon fallback).
- `coingeckoId` — nothing on chain supplies it; it can be added later without a version bump.

## Findings that shaped the design

Probed against `wss://entrypoint-finney.opentensor.ai:443` on 2026-09-25.

- `SubnetInfoRuntimeApi.get_all_dynamic_info` cannot be decoded with the repo's `substrate-interface==1.7.4` /
  `scalecodec==1.2.11`: the API is not in its runtime-call registry, and scalecodec cannot parse metadata V15 (where
  runtime-API types live).
- The same data is in storage, readable through metadata V14 with the existing library:
  `SubtensorModule.NetworksAdded` (129 subnets), `SubtensorModule.SubnetIdentitiesV3` (122 identities, 99 with a
  `logo_url`), `SubtensorModule.TokenSymbol` (129, decoded as strings such as `α`, `ش`).
- Of the 99 `logo_url`s: 75 are raster images that download fine (PNG/JPEG/WebP), 9 are SVG, 15 are broken (404/402,
  HTML pages, timeouts). Files reach 2.6 MB. Hot-linking them is not viable.

Therefore: read storage, not the runtime API; normalise every logo; keep the previous logo when a source breaks.

## Output contract

```
bittensor/v1/subnets.json
icons/bittensor/subnets/sn<netuid>-<hash8>.png
```

`subnets.json`:

```json
{
  "subnets": [
    {
      "netuid": 1,
      "name": "Apex",
      "symbol": "α",
      "logo": "https://raw.githubusercontent.com/novasamatech/nova-utils/master/icons/bittensor/subnets/sn1-3fa9c21e.png"
    },
    { "netuid": 17, "name": null, "symbol": "ⴷ", "logo": null }
  ]
}
```

- One entry per netuid with `NetworksAdded == true`, root netuid 0 included, sorted by `netuid` ascending.
- `name`: `subnet_name` from `SubnetIdentitiesV3`, whitespace-trimmed; `null` when there is no identity or the name is
  empty. Clients display `SN<netuid>` for `null`.
- `symbol`: `TokenSymbol` value as a string.
- `logo`: absolute raw-GitHub URL of the normalised PNG; `null` means "use the Generic identicon".
- `<hash8>`: first 8 hex chars of the sha256 of the PNG bytes. A changed logo gets a new URL, so caching is safe.
- No timestamp field: an unchanged chain state yields a byte-identical file and therefore no PR.
- Single file, no dev/prod pair: it mirrors chain state, there is nothing to curate or promote.
- `v1/` directory so the schema can evolve without breaking shipped clients.

Logo PNGs: 256×256, RGBA, source fitted inside the square with aspect ratio preserved and transparent padding;
metadata stripped. Clients apply the circle mask.

## Components

All code in `scripts/bittensor/`. Each unit is testable on its own.

### `chain_source.py`

`fetch_subnets() -> list[Subnet]`, where `Subnet` is a dataclass `(netuid: int, name: str | None, symbol: str,
logo_url: str | None)`.

- Node list: the Bittensor entry (chainId `2f0555cc76fc2840a25a6ea3b9637146806f1f44b090c175ffde2a7e5ab36c03`) in the
  latest `chains/vNN/chains.json`, resolved via `latest_config_version()`. Nodes are tried in order; the first that
  answers all three queries wins.
- Queries: `query_map` over `NetworksAdded`, `SubnetIdentitiesV3`, `TokenSymbol`.
- Raises `ChainSourceError` if no node answers.

### `logo_normalizer.py`

`normalize(raw: bytes) -> bytes` (PNG) or raises `LogoError`.

- Format detected from content, not URL or `Content-Type`: SVG (XML with an `<svg` root) → cairosvg rasterised at
  256 px; everything else → Pillow (PNG, JPEG, WebP, GIF first frame, ICO largest frame). HTML or undecodable input →
  `LogoError`.
- Fit into 256×256 transparent canvas, centred, aspect preserved, LANCZOS resampling.
- Deterministic encoding (no metadata chunks, fixed compression level) so identical input produces identical bytes.

### `update_subnets.py` — entry point

Run as `make update-bittensor-subnets`.

1. Load the current `bittensor/v1/subnets.json` (absent on first run → empty).
2. `fetch_subnets()`.
3. Download every `logo_url` in parallel: 15 s timeout, 5 MB body cap, browser User-Agent.
4. `normalize()` each download.
5. Merge (a pure function, `merge(previous, subnets, logos) -> Result(entries, files_to_write, files_to_delete)`):
   - download + normalise OK → new hashed file;
   - failure and the previous entry for that netuid had a logo → keep the previous logo;
   - failure with no previous logo → `null`;
   - `logo_url` absent on chain → `null`.
6. Write PNGs, write `subnets.json` (2-space indent, `ensure_ascii=False`, trailing newline), delete PNGs in
   `icons/bittensor/subnets/` no longer referenced.
7. Print a summary: updated / kept previous / no logo, with the failing netuids and reasons.

Abort (non-zero exit, no files touched):

- `ChainSourceError` — no RPC node answered.
- The chain returned fewer than half as many subnets as the current file holds — guard against wiping data on a bad
  node response.

## Automation

`.github/workflows/update_bittensor_subnets.yaml`, modelled on `update_chains_preconfigured.yaml`:

- `on: schedule: cron '0 6 * * *'` and `workflow_dispatch`.
- Steps: checkout → `./.github/workflows/setup-path` → Python 3.10 → `sudo apt-get install -y libcairo2` → `make init`
  → `make update-bittensor-subnets` → `./.github/workflows/make-pull-request` with
  `commit-files: bittensor/**, icons/bittensor/**`, `branch-name: update-bittensor-subnets`, `pr-base: master`.
- A fixed branch name means an unmerged PR is updated in place; no diff means no PR.
- `alert` job posts to Telegram on failure, same as the other scheduled workflows.

## Dependencies

Add `Pillow` and `cairosvg` to `pyproject.toml` and regenerate `poetry.lock`. Local SVG rendering needs the system
cairo library (`brew install cairo` on macOS); ubuntu runners get it from the apt step.

## Testing

Offline, no RPC or network, under `tests/bittensor/`, run with `pytest tests/bittensor`:

- `logo_normalizer`: PNG, JPEG, ICO and SVG inputs → 256×256 RGBA PNG; non-square input keeps aspect ratio with
  transparent padding; HTML and random bytes raise `LogoError`; same input → identical bytes.
- `merge`: failed download keeps the previous logo; failed download without previous → `null`; `logo_url` removed →
  `null` and old file scheduled for deletion; unchanged logo → same filename, nothing written or deleted.
- Abort guard: fewer than half the previous subnet count raises.
- Repo consistency: every `logo` in `bittensor/v1/subnets.json` resolves to an existing file under
  `icons/bittensor/subnets/`, and no unreferenced PNGs exist there.

The live-RPC integration suite is not touched.

## Rollout

The feature PR includes the first generated snapshot (script run locally), so reviewers see real output. After merge,
the daily workflow takes over.
