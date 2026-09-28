# Remove unprofitable staking options (dev)

## Goal

Stop offering in-app staking for networks where Nova no longer runs a profitable
validator/collator/pool or where the network is dead, and point users to where
they can manage their stake instead.

## Scope

Networks losing staking (utility asset `staking` field removed):

| Network | chainId prefix | Removed types | Where to manage stake |
|---|---|---|---|
| Aleph Zero | 70255b4d28de | aleph-zero, nomination-pools | https://dashboard.alephzero.org |
| Vara | fe1b4c55fd4d | relaychain, nomination-pools | https://staking.vara.network |
| Avail | b91746b45e03 | relaychain, nomination-pools | https://staking.availproject.org |
| Polkadex | 3920bcb4960a | relaychain | https://explorer.polkadex.ee |
| Ternoa | 6859c81ca95e | relaychain | Polkadot.js (staking site is dead) |
| Moonbeam | fe58ea77779b | parachain | Polkadot.js (dead) |
| Moonriver | 401a1f9dca3d | parachain | Polkadot.js (dead) |
| Zeitgeist | 1bf2a2ecb4a8 | parachain | Polkadot.js (dead) |
| Manta Atlantic | f3c7ad88f6a8 | parachain | Polkadot.js (dead) |
| Aleph Zero Testnet | 05d5279c52c4 | aleph-zero, nomination-pools | — (dev only) |
| Vara Testnet | 525639f713f3 | relaychain | — (dev only) |
| Avail Turing Testnet | d3d2f3a3495d | relaychain, nomination-pools | — (dev only) |
| Ternoa Alphanet | 18bcdb75a0bb | relaychain | — (dev only) |

**Mythos keeps staking** — there is no alternative staking app for it yet.

## Client behaviour (verified in nova-wallet-ios ae6f7d2f8, nova-wallet-android 3d37ba90c)

- A chain appears on the Staking dashboard only if its utility asset has a
  supported `staking` value. Removing the field hides it entirely, including
  for users with active/unbonding stakes; there is no other in-app path to
  unbond/redeem. Accepted: users manage existing stakes externally.
- Pool stake stops being counted in total balance; reward history filters
  disappear. Balance locks remain visible in the locks breakdown.
- `stakingWiki` and `externalApi.staking*` are read only by staking screens,
  so they are left in place (cleanup together with SubQuery shutdown later).
- No staking banner domain exists; banners are shown on Assets. The staking
  dashboard shows the general (chainId-less) announcement.

## Changes (dev files only)

1. `chains/v22/chains_dev.json` — delete `staking` from the utility asset of the
   13 chains above.
2. `staking/validators/v1/nova_validators_dev.json` — delete Aleph Zero and
   Avail entries from `preferred` and `excluded`. Mythos entries stay.
3. `banners/v2/content/assets/banners_dev.json` — add one banner (new UUID),
   reusing existing `staking_promo_banner_picture.png` and an existing
   background; `action` =
   `https://docs.novawallet.io/nova-wallet-wiki/staking/removed-staking-options`.
   Add its `title`/`details` to every `localized_dev/*.json` (iOS has no language
   fallback, and a banner without a localized entry is dropped on both
   platforms). English:
   - title: "Staking changes"
   - details: "AZERO, VARA, AVAIL & other staking moved out of Nova. See where to manage your stake →"
4. `announcements/v1/announcements_dev.json` — unchanged; it already has the
   general warning announcement linking to the same wiki page.
5. Wiki page draft (markdown, outside the repo) for the docs team: per-network
   table of where to manage/withdraw the stake.

## Out of scope

- Prod promotion (`chains.json`, `nova_validators.json`, `banners.json` +
  `localized/`, new `announcements.json`) — separate PR, only after the wiki
  page is published (the banner/announcement link is 404 until then).
- Removing hardcoded chain logic in the apps (dead code once config is gone).
- Removing `stakingWiki` / `externalApi.staking*` and SubQuery indexers.

## Verification

`make check-chains-file`, pre-commit on changed files, JSON diff shows only
`staking` keys removed from the 13 chains.
