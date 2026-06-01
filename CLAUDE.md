# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

This is a **DayZ dedicated-server mission folder** for a **one-life deathmatch** server (Chernarus-based, judging by the map data). It is *not* a code project — there is no build step, package manager, or test suite. It is the live set of XML / JSON / `.c` config files the DayZ server engine reads at startup. Editing these files changes server behavior directly.

Players spawn fully geared (one random loadout from `custom/`) and fight; there is one life per spawn. The economy is configured so loot, infected, and players are managed by the Central Economy (CE).

## Deployment — read before editing

Changes are deployed **automatically by FTP on every push to `develop`** via `.github/workflows/deploy.yml` (SamKirkland/FTP-Deploy-Action). Notes:

- Only **changed files** are uploaded (incremental; tracked by `.ftp-deploy-sync-state.json` on the server). `dangerous-clean-slate` is `false` — the action never wipes the server.
- **Excluded from deploy:** `.git`, `.github`, `node_modules`, `vendor`, **all `*.md` files**, `.gitignore`, `.gitattributes`. So this CLAUDE.md and any docs never reach the server.
- `develop` is the main working branch. Pushing to it ships to the live server — treat commits to `develop` as a production deploy.

## Validate before committing

There is no test runner. The available validation is XML well-formedness:

```bash
xmllint --noout db/types.xml          # validate any XML file you touched
python3 -m json.tool <file.json> >/dev/null   # validate any JSON file you touched
```

Always validate edited XML/JSON before committing — a malformed file can prevent the server economy from loading.

## Layout

### Root config files
- `init.c` — mission server logic (Enforce Script). `main()` runs economy init + a seasonal date reset (resets the world clock to Sep 20). `CustomMission::StartingEquipSetup` adds starting items (bandage, random chemlight, random fruit) and randomizes clothing health 0.45–0.65 on spawn.
- `cfggameplay.json` — gameplay tuning. `PlayerData.spawnGearPresetFiles` is the list of all 36 `custom/*.json` loadouts the server picks from at spawn. `disableRespawnDialog`/`disableRespawnInUnconsciousness` are on (deathmatch flow).
- `cfgeconomycore.xml` — CE root classes + global CE defaults/logging toggles.
- `cfgspawnabletypes.xml` — per-item attachment/cargo/ammo spawn presets (e.g. which mag/optic a weapon spawns with).
- `cfgrandompresets.xml` — named random cargo/attachment groups (e.g. `ZedCargo1`) referenced by spawnable types.
- `cfgeventspawns.xml`, `cfgeventgroups.xml` — dynamic event spawn positions and group definitions.
- `cfgplayerspawnpoints.xml` — where players spawn.
- `cfgweather.xml`, `cfgenvironment.xml`, `cfgEffectArea.json` — weather, environment (animal territories index), effect areas (e.g. contaminated zones).
- `cfglimitsdefinition.xml` / `cfglimitsdefinitionuser.xml` — valid loot `usage`/`category`/`tag`/`value` flag vocabularies. User file defines custom flags (e.g. the `Deathmatch` usage).
- `mapgroup*.xml`, `mapcluster*.xml`, `areaflags.map` — map object/loot-position data (large, engine-generated; rarely hand-edited). `mapgroupproto.xml` defines loot points per building type.

### `db/` — economy database
- `types.xml` — **the loot table.** Every spawnable item's `nominal`, `min`, `lifetime`, `restock`, quantities, `cost`, `<flags .../>`, and `<usage>` tags. The `usage name="Deathmatch"` tag + `count_in_map` flags control what actually spawns on this server.
- `economy.xml` — master CE on/off switches for dynamic/zombies/vehicles/players/etc. (`init`/`load`/`respawn`/`save`).
- `globals.xml` — global CE variables (cleanup lifetimes, max counts, etc.).
- `events.xml` — dynamic event definitions. `messages.xml` — server broadcast/shutdown messages.
- `types.xml.bak` — a backup; do not deploy/rely on it.

### `custom/` — spawn loadouts (36 files)
Each file is one full-gear spawn preset, named `<assault>-<sniper>.json` (e.g. `m16a2-vss.json` = M16A2 assault + VSS sniper). Assault weapons: `ak74`, `aks74u`, `augshort`, `famas`, `m16a2`, `vikhr`. Snipers: `asval`, `cz527`, `cz550`, `scout`, `ssg82`, `vss` → 6×6 = 36 combinations. All 36 are listed in `cfggameplay.json`.

Structure of each loadout:
- `attachmentSlotItemSets[]` — one entry per equipment slot (`Vest`, `Headgear`, `Gloves`, `Body`, `Legs`, `Feet`, `Eyewear`, `Mask`, `Hips`, `Hands`, `shoulderL`). Each slot's `discreteItemSets[]` lists the item variants (the engine picks one by `spawnWeight`).
  - The **assault weapon** is in the `Hands` slot; the **sniper** is in `shoulderL`. A weapon's attachments + magazine are listed as strings in its `simpleChildrenTypes` (e.g. `"Mag_AK74_45Rnd"`).
- `discreteUnsortedItemSets[]` — loose inventory cargo. Contains a single `Cargo1` set whose `complexChildrenTypes[]` holds the actual items (bandages, epinephrine, spare magazines, etc.). Each item object is `{ itemType, attributes{healthMin/Max,quantityMin/Max}, quickBarSlot }`.

When adding items across all loadouts, prefer a Python script that loads each JSON, mutates it, and writes back with `json.dumps(d, indent=4) + "\n"` — this matches the existing 4-space style and trailing newline. Copy item identifiers (e.g. magazine names) exactly from the file's own weapon `simpleChildrenTypes`, since they differ per weapon (note inconsistent casing: `Mag_CZ550_10rnd` vs `Mag_Scout_5Rnd`).

### `env/` — animal/zombie territory definitions (referenced by `cfgenvironment.xml`).

## Conventions
- Indentation in `custom/*.json` is 4 spaces; root XML files use tabs in some files and spaces in others — match the file you're editing.
- Custom server content is tagged with the `Deathmatch` usage flag in `types.xml` so it spawns on this server; keep that tag on items meant to spawn.
