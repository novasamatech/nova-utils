# Remove Staking Options (dev) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove in-app staking for 9 mainnets + 4 testnets in dev config, drop their preferred validators, and add an Assets banner pointing to the wiki page about removed staking options.

**Architecture:** Pure JSON data edits in dev files only (spec: `docs/superpowers/specs/2026-09-28-remove-staking-options-design.md`). `chains_dev.json` and `nova_validators_dev.json` round-trip byte-exactly through `json.dumps(indent=4|2, ensure_ascii=False) + "\n"`, so they are edited with a load/modify/dump Python snippet run from the repo root. Banner files are edited with the same approach where they round-trip (localized files, indent 4); `banners_dev.json` uses a mixed indent and is edited by hand.

**Tech Stack:** JSON, Python 3 (stdlib), pre-commit (`make check-chains-file`).

---

### Task 1: Remove `staking` from 13 chains in chains_dev.json

**Files:**
- Modify: `chains/v22/chains_dev.json`

- [ ] **Step 1: Assert current state (the "failing test")**

```bash
python3 - <<'EOF'
import json
IDS = {
    "70255b4d28de0fc4e1a193d7e175ad1ccef431598211c55538f1018651a0344e",  # Aleph Zero
    "fe1b4c55fd4d668101126434206571a7838a8b6b93a6d1b95d607e78e6c53763",  # Vara
    "b91746b45e0346cc2f815a520b9c6cb4d5c0902af848db0a80f85932d2e8276a",  # Avail
    "3920bcb4960a1eef5580cd5367ff3f430eef052774f78468852f7b9cb39f8a3c",  # Polkadex
    "6859c81ca95ef624c9dfe4dc6e3381c33e5d6509e35e147092bfbc780f777c4e",  # Ternoa
    "fe58ea77779b7abda7da4ec526d14db9b1e9cd40a217c34892af80a9b332b76d",  # Moonbeam (PAUSED)
    "401a1f9dca3da46f5c4091016c8a2f26dcea05865116b286f60f668207d1474b",  # Moonriver (PAUSED)
    "1bf2a2ecb4a868de66ea8610f2ce7c8c43706561b6476031315f6640fe38e060",  # Zeitgeist (PAUSED)
    "f3c7ad88f6a80f366c4be216691411ef0622e8b809b1046ea297ef106058d4eb",  # Manta Atlantic
    "05d5279c52c484cc80396535a316add7d47b1c5b9e0398dd1f584149341460c5",  # Aleph Zero Testnet
    "525639f713f397dcf839bd022cd821f367ebcf179de7b9253531f8adbe5436d6",  # Vara Testnet
    "d3d2f3a3495dc597434a99d7d449ebad6616db45e4e4f178f31cc6fa14378b70",  # Avail Turing Testnet
    "18bcdb75a0bba577b084878db2dc2546eb21504eaad4b564bb7d47f9d02b6ace",  # Ternoa Alphanet
}
d = json.load(open("chains/v22/chains_dev.json"))
left = [c["name"] for c in d if c["chainId"] in IDS and any("staking" in a for a in c["assets"])]
assert not left, f"still stakeable: {left}"
EOF
```

Expected: `AssertionError: still stakeable: [...13 names...]`

- [ ] **Step 2: Remove the field**

Run the same script from Step 1, replacing its last three lines with:

```python
path = "chains/v22/chains_dev.json"
d = json.load(open(path))
for c in d:
    if c["chainId"] in IDS:
        for a in c["assets"]:
            a.pop("staking", None)
open(path, "w").write(json.dumps(d, indent=4, ensure_ascii=False) + "\n")
```

- [ ] **Step 3: Re-run Step 1 script**

Expected: no output, exit 0.

- [ ] **Step 4: Check the diff contains only staking removals and Mythos is untouched**

```bash
git diff --stat chains/v22/chains_dev.json
git diff -U0 chains/v22/chains_dev.json | grep '^[+-] ' | grep -v -E '^-\s+("staking": \[|"(relaychain|parachain|nomination-pools|aleph-zero)",?|\],?)$'
```

Expected: stat shows only deletions (plus possibly a few `+`/`-` lines that only change a trailing comma on the preceding line); the grep prints only those comma-adjusted lines. Then:

```bash
python3 -c "import json;print([a.get('staking') for c in json.load(open('chains/v22/chains_dev.json')) if c['name']=='Mythos' for a in c['assets'] if a.get('staking')])"
```

Expected: `[['mythos']]`

- [ ] **Step 5: Commit**

```bash
git add chains/v22/chains_dev.json
git commit -m "Remove staking for AZERO, VARA, AVAIL, PDEX, CAPS, GLMR, MOVR, ZTG, MANTA and testnets in dev"
```

### Task 2: Drop Aleph Zero and Avail from nova_validators_dev.json

**Files:**
- Modify: `staking/validators/v1/nova_validators_dev.json`

- [ ] **Step 1: Remove entries**

```bash
python3 - <<'EOF'
import json
path = "staking/validators/v1/nova_validators_dev.json"
DROP = {
    "70255b4d28de0fc4e1a193d7e175ad1ccef431598211c55538f1018651a0344e",  # Aleph Zero
    "b91746b45e0346cc2f815a520b9c6cb4d5c0902af848db0a80f85932d2e8276a",  # Avail
}
d = json.load(open(path))
for section in d.values():
    for k in DROP:
        section.pop(k, None)
open(path, "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
EOF
```

- [ ] **Step 2: Verify**

```bash
grep -c -E '70255b4d28de|b91746b45e03' staking/validators/v1/nova_validators_dev.json; grep -c f6ee56e9c527 staking/validators/v1/nova_validators_dev.json
```

Expected: `0` then `1` or more (Mythos kept).

- [ ] **Step 3: Commit**

```bash
git add staking/validators/v1/nova_validators_dev.json
git commit -m "Remove Aleph Zero and Avail preferred validators in dev"
```

### Task 3: Add the "Staking changes" banner (dev)

**Files:**
- Modify: `banners/v2/content/assets/banners_dev.json`
- Modify: `banners/v2/content/assets/localized_dev/{en,es,fr,hu,id,in,it,ja,ko,pl,pt,ru,tr,vi,zh}.json`

- [ ] **Step 1: Insert the banner as the first element of `banners_dev.json`** (keep the file's 4/7-space indentation):

```json
    {
       "id": "b792eebc-ccd3-47f0-8ddc-17995749d3cc",
       "background": "https://raw.githubusercontent.com/novasamatech/nova-utils/master/banners/v2/resources/backgrounds/red_promo_banner_background.png",
       "image": "https://raw.githubusercontent.com/novasamatech/nova-utils/master/banners/v2/resources/images/staking_promo_banner_picture.png",
       "clipsToBounds": false,
       "action": "https://docs.novawallet.io/nova-wallet-wiki/staking/removed-staking-options"
    },
```

- [ ] **Step 2: Add localized texts (inserted first in each file)**

```bash
python3 - <<'EOF'
import json
ID = "b792eebc-ccd3-47f0-8ddc-17995749d3cc"
T = {
    "en": ("Staking changes", "AZERO, VARA, AVAIL & other staking moved out of Nova. See where to manage your stake →"),
    "ru": ("Изменения в стейкинге", "Стейкинг AZERO, VARA, AVAIL и других сетей больше не в Nova. Где управлять стейком →"),
    "es": ("Cambios en staking", "El staking de AZERO, VARA, AVAIL y otras redes ya no está en Nova. Dónde gestionar tu stake →"),
    "fr": ("Changements du staking", "Le staking d'AZERO, VARA, AVAIL et d'autres réseaux quitte Nova. Où gérer votre stake →"),
    "hu": ("Staking változások", "Az AZERO, VARA, AVAIL és más hálózatok stakingje már nem érhető el a Novában. Hol kezelheted a stake-edet →"),
    "id": ("Perubahan staking", "Staking AZERO, VARA, AVAIL & lainnya tidak lagi tersedia di Nova. Lihat tempat mengelola stake Anda →"),
    "in": ("Perubahan staking", "Staking AZERO, VARA, AVAIL & lainnya tidak lagi tersedia di Nova. Lihat tempat mengelola stake Anda →"),
    "it": ("Modifiche allo staking", "Lo staking di AZERO, VARA, AVAIL e altre reti non è più su Nova. Scopri dove gestire il tuo stake →"),
    "ja": ("ステーキングの変更", "AZERO、VARA、AVAILなどのステーキングはNovaでの提供を終了しました。ステークの管理先はこちら →"),
    "ko": ("스테이킹 변경 안내", "AZERO, VARA, AVAIL 등의 스테이킹은 더 이상 Nova에서 지원되지 않습니다. 스테이크 관리 방법 보기 →"),
    "pl": ("Zmiany w stakingu", "Staking AZERO, VARA, AVAIL i innych sieci nie jest już dostępny w Nova. Zobacz, gdzie zarządzać stakiem →"),
    "pt": ("Mudanças no staking", "O staking de AZERO, VARA, AVAIL e outras redes não está mais na Nova. Veja onde gerenciar seu stake →"),
    "tr": ("Staking değişiklikleri", "AZERO, VARA, AVAIL ve diğer ağların stakingi artık Nova'da yok. Stake'inizi nerede yöneteceğinizi görün →"),
    "vi": ("Thay đổi về staking", "Staking AZERO, VARA, AVAIL và các mạng khác không còn trên Nova. Xem nơi quản lý stake của bạn →"),
    "zh": ("质押变更", "AZERO、VARA、AVAIL 等质押已不再在 Nova 中提供。查看在哪里管理您的质押 →"),
}
for lang, (title, details) in T.items():
    path = f"banners/v2/content/assets/localized_dev/{lang}.json"
    d = json.load(open(path))
    d = {ID: {"title": title, "details": details}, **{k: v for k, v in d.items() if k != ID}}
    open(path, "w").write(json.dumps(d, indent=4, ensure_ascii=False) + "\n")
EOF
```

- [ ] **Step 3: Verify every banner id has a localization in every language**

```bash
python3 - <<'EOF'
import json, glob
ids = [b["id"] for b in json.load(open("banners/v2/content/assets/banners_dev.json"))]
for f in sorted(glob.glob("banners/v2/content/assets/localized_dev/*.json")):
    missing = [i for i in ids if i not in json.load(open(f))]
    print(f, "missing:", missing)
EOF
```

Expected: every line prints `missing: []`. Also `curl -sI` both image URLs (`.../backgrounds/red_promo_banner_background.png`, `.../images/staking_promo_banner_picture.png`) → `HTTP/2 200`.

- [ ] **Step 4: Commit**

```bash
git add banners/v2/content/assets
git commit -m "Add dev banner about removed staking options"
```

### Task 4: Validate and draft the wiki page

- [ ] **Step 1:** `make check-chains-file` and `.venv/bin/pre-commit run --files <all changed files>` → all Passed/Skipped.
- [ ] **Step 2:** Write the wiki draft to the session scratchpad (`removed-staking-options.md`, not committed): intro, table network → where to manage/withdraw stake (Avail → staking.availproject.org; Aleph Zero → dashboard.alephzero.org; Vara → staking.vara.network; Polkadex → explorer.polkadex.ee; Ternoa → Polkadot.js per docs.ternoa.network staking guide; Moonbeam, Moonriver, Zeitgeist, Manta → Polkadot.js), short "how to unbond via Polkadot.js" steps, note that funds are safe and locks are still visible in Nova.
- [ ] **Step 3:** Push branch, open PR to `master` titled "Remove unprofitable staking options (dev)" — only after the user confirms.
