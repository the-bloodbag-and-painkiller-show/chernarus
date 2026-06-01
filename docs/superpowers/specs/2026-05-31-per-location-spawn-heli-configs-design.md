# Per-Location Spawn & Heli-Crash Configs — Design

**Date:** 2026-05-31
**Status:** Approved (design); implementation pending

## Context & Goal

This server is a one-life, full-gear deathmatch. The larger vision is a bot that, every
30 minutes, forces the entire server into a single Chernarus town, restarts the server, and
posts the current/next location plus kill leaderboards via `db/messages.xml`.

That vision has three independent pieces:

1. **Per-location config files** (this spec) — a ready-to-swap `cfgplayerspawnpoints.xml` and
   `cfgeventspawns.xml` for each town.
2. **Rotation bot** — picks a town, swaps the two files into the mission root, restarts. *(separate spec)*
3. **`messages.xml` leaderboards** — current/next location + all-time/monthly/weekly top killers,
   which needs a kill-tracking data source. *(separate spec)*

**This spec covers only piece #1.** It produces drop-in config files so the future bot stays a
trivial file-copy + restart.

## Decisions (from brainstorming)

- **Location pool:** all **78** towns from `docs/town-centers.json` (hamlets included).
- **Spawn layout:** a **ring** of evenly-spaced spawn points around each town center; radius and
  point count scale with town size.
- **Heli crashes:** **scattered across the town footprint** in **open ground** (off buildings).
- **Other events:** keep `Infected*` + `Loot` blocks unchanged; **strip** all events that have no
  active definition in `db/events.xml` (already-dead `Vehicle*`, `Animal*`, static crashes, etc.).
  Only `StaticHeliCrash` is relocated.
- **Generation approach:** a committed Python generator (`locations/generate.py`) plus its
  committed output. The bot consumes finished files; logic lives in one reviewable place.

### Current live-event state (verified in `db/events.xml`)

Only these have `active=1` definitions, so only these actually spawn:
- 16 `Infected*` variants (nominal 50 each)
- `Loot`
- `StaticHeliCrash` (nominal 3, `position=fixed`, `zone r=45`)

Everything else listed in `cfgeventspawns.xml` (`Vehicle*`, `Animal*`, `StaticTrain`,
`StaticContaminatedArea`, `StaticSantaCrash`, `StaticPoliceCar`, `StaticMilitaryConvoy`, …) has no
definition in `events.xml` and is inert — safe to strip from the per-location files.

> Note: the brainstorm started from "everything except Loot is disabled," but verification showed
> Infected and HeliCrash are live. Decision: leave Infected/Loot untouched; this spec does not
> change zombie behavior.

## Inputs

- `docs/town-centers.json` — 78 towns: `name`, `cat` (category), `cx`/`cz` (center), `n` (buildings).
- `mapgrouppos.xml` — 11,680 building objects (`pos="x y z"`, name=type) for heli clearance checks.
- Current `cfgplayerspawnpoints.xml` and `cfgeventspawns.xml` — used as structural templates
  (keep their `spawn_params`/`generator_params`/`group_params` and the `Infected*`/`Loot` blocks).

## Output

```
locations/
  generate.py                      # the generator (committed artifact)
  index.json                       # manifest of all 78 towns (for the bot)
  <slug>/
    cfgplayerspawnpoints.xml       # ring of spawns at this town
    cfgeventspawns.xml             # heli crashes relocated here; dead events stripped
```

- **Slug:** kebab-case of the town name (matches `custom/` loadout naming), e.g.
  `Novy Sobor` → `novy-sobor`, `Belaya Polana` → `belaya-polana`.
- **`index.json`** entry per town:
  `{ name, slug, category, center_x, center_z, spawn_radius, spawn_points, heli_count }`.

## Component 1 — Spawn ring (`cfgplayerspawnpoints.xml`)

Keep the existing `spawn_params` / `generator_params` / `group_params` blocks. Replace **all**
`generator_posbubbles` groups in **all three** sections (`fresh`, `hop`, `travel`) with a single
ring group centered on the town, so a player lands at the active town regardless of entry type.

**Ring** = `N` points evenly spaced on a circle of radius `R` about `(center_x, center_z)`:
`x = cx + R·cos(2πi/N)`, `z = cz + R·sin(2πi/N)` for `i in 0..N-1`.

| Category | Ring radius `R` | Ring points `N` |
|---|---:|---:|
| Hamlet | 80 m | 10 |
| Village | 110 m | 12 |
| Town | 150 m | 14 |
| Small City | 180 m | 16 |
| Large City | 220 m | 18 |

Each ring point is a spawn *bubble*; `generator_params` grid expands each into many real spawn
slots, so concurrent player count is not capped by `N`. Set `min_dist_player` to a tighter
**20–60 m** range (currently 65–150 in `fresh`) so a full lobby can all spawn at one town without
placement failures.

All radii / counts / min-distances are tunable constants at the top of `generate.py`.

## Component 2 — Heli crashes + event stripping (`cfgeventspawns.xml`)

Per town, starting from the current file:

- **Keep unchanged:** the 8 `Infected*` position blocks and `Loot`.
- **Strip:** every event whose name has no `active=1` definition in `db/events.xml`.
- **Relocate `StaticHeliCrash`:** replace its position list with **8–10 open positions** found by:
  1. Grid-sample (~15 m spacing) within the footprint (radius `R + 50 m` of center).
  2. Reject any sample within a **clearance distance** of the nearest `mapgrouppos.xml` building
     — default **30 m**, bumped for known large building types (tenements, apartments, hangars,
     industrial). This keeps crashes off structures.
  3. **Farthest-point sample** ~8–10 survivors so positions spread across the town, not clumped.
  4. If a dense town yields too few at 30 m, relax clearance in 2 m steps to a floor (~22 m) and
     log a warning for that town.
  - Preserve `zone r="45"`, `nominal=3`, and `a="-1"` (random orientation).

### Large-building clearance table (initial)

A small name→clearance map for the biggest footprints (e.g. `Land_Tenement*`, `Land_House_2*`,
`Land_Industrial*`, `Land_Hangar*`, `Land_Warehouse*`). Default clearance 30 m; listed types use
40–50 m. Refined empirically if any crash still clips a structure.

## Validation

- `xmllint --noout` on every generated XML (well-formedness gate).
- Per-town sanity asserts: spawn file has `N` ring positions in all three sections; event file
  contains `Loot` + all `Infected*` blocks and a `StaticHeliCrash` block with heli-count positions;
  no stripped event names remain.
- Generator prints a summary: towns processed, heli positions per town, any clearance-relaxation
  warnings.

## Out of Scope (separate specs)

- The rotation/restart bot (piece #2).
- `messages.xml` leaderboard generation (piece #3).
- Whether `locations/` is included in the FTP deploy (decided with the bot's runtime location).
- Any change to zombie/loot economy behavior.

## Open Items / Risks

- **Spawn tuning is theoretical** until playtested; ring radii and `min_dist_player` may need
  adjustment once real lobbies spawn in.
- **Clearance is a point-distance heuristic**, not true geometry; the large-building table is the
  mitigation and may need tuning per offending town.
- **`hop`/`travel` necessity:** filling all three sections is the safe choice; if only `fresh` is
  ever used in this deathmatch flow, the extra sections are harmless.
