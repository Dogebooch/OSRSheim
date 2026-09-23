# OSRSheim

Valheim 1.0 modded to play like Old School RuneScape: skills you grind to 100,
gear you unlock by level, drop tables worth farming, Slayer, riddle-clues, a
bank and a collection log. It still looks, sounds and reads like Valheim. Two
players (Doug and Sven) on a rented dedicated server.

**Design principle:** copy OSRS mechanics. Do not copy OSRS names, characters,
items, quest text or audio ([`CLAUDE.md`](CLAUDE.md)).

**Balance:** each biome fights, gears and pays like vanilla Valheim; the run is
longer, not easier or richer. Vanilla's loop is "new biome, new gear, same
fight". Here, skill gates make magic, abilities and rares something you unlock.
Run length and balance issues: [#81](https://github.com/Dogebooch/OSRSheim/issues/81).

## The loops

| Loop (OSRS analogue) | Valheim version | Ref |
|---|---|---|
| Skills (skills) | grind to 100 at half XP; mapping in [§4](RESEARCH.md#4-skill-mapping) | §4, §5 |
| Gear gates (level requirements) | WIRSL skill levels on gear, tools, bait | §6 |
| Drop tables (drop tables) | coins, gems, rares, uniques, pets, superiors | §7, §12 |
| Slayer (Slayer) | KG Slayer tasks + EpicLoot bounties | §10, §11 |
| Bone prayers (Prayer) | KG `chapel` buffs paid in bones | §11 |
| Herb runs (Herblore) | crops -> meadbase -> potion, Alchemy-gated | §6, §11 |
| Riddle-stones (clue scrolls) | four tiers, opened at a KG gambler | §7, §11 |
| Biome oaths (achievement diaries) | 8 biomes of tasks, a cape and a key each | §11 |
| Collection log (collection log) | one KG quest per collectible, lit when found | §11 |
| KG Marketplace (bank, shops, quests, hiscores) | NPCs placed in town | §11 |
| Earned waystones (teleports) | one KG waystone per sworn biome | §11 |

§N = section of [`RESEARCH.md`](RESEARCH.md) or the [`research/`](research) file its map names.

## Status

[`STATE.md`](STATE.md): what is live, what is next.

## Repo map

| Folder | Holds |
|---|---|
| [`config/`](config) | mod configs; source of truth for the Gale profile and the host |
| [`loot/`](loot) | drop-rate CSVs; input to the loot and collection-log generators |
| [`reference/`](reference) | mod manifest, verified prefab names, wackydb base dumps, game data (`game-data/`), measured rates, audits |
| [`research/`](research) | reference topic files (loot, marketplace, gating, ...); map in `RESEARCH.md` |
| [`scripts/`](scripts) | generators, validators, sync, doc hooks |
| [`staging/`](staging) | changes built but not yet applied to `config/` |
| [`archive/`](archive) | first build's docs and config snapshot; read-only |

Generated, never hand-edited: `config/drop_that.character_drop*.cfg`,
`config/drop_that.drop_table.cfg`, the collection-log cfgs, `reference/mods.tsv`.
Generators and enforced limits: [`CLAUDE.md` Rules](CLAUDE.md#rules).

## How a change flows

| Step | Where |
|---|---|
| 1. Edit | repo `config/` (or `loot/` + generator) |
| 2. Push to the Gale profile | `scripts\sync-configs.ps1 -Push` |
| 3. Pre-flight | `python scripts\post-build-check.py` |
| 4. Test | ModTest world |
| 5. Deploy | host ([§15](RESEARCH.md#15-server-setup)) |

Profile and host are downstream; edits there get overwritten.

## For agent sessions

| Order | Doc |
|---|---|
| 1 | [`CLAUDE.md`](CLAUDE.md): rules, paths, doc style (Codex enters via [`AGENTS.md`](AGENTS.md)) |
| 2 | [`STATE.md`](STATE.md): status |
| 3 | [`RESEARCH.md`](RESEARCH.md): the reference hub, then the [`research/`](research) file for the topic |

The AI records and proposes; Doug decides. In-game test checklists live in
[GitHub issues](https://github.com/Dogebooch/OSRSheim/issues).

## Glossary

| Term | Meaning |
|---|---|
| Gielheim | the real world, created on the host once the stack is stable |
| ModTest | the local test world |
| WIRSL | WackyMole ItemRequiresSkillLevel: skill-level gates on items |
| KG | KG Marketplace: traders, bank, quests, teleporters, hiscores |
| CLLC | Creature Level and Loot Control: star effects on superiors; loot left vanilla (§9) |
| Drop That / Spawn That | config mods for creature and object drops / spawns |
| Superiors | rare 3-level elites with an effect, one per biome, own drop table (§12) |
| wackydb clones | custom items cloned from vanilla prefabs via WackysDatabase (§8) |
| §N | a numbered section of the reference; `RESEARCH.md` maps each to its file |
