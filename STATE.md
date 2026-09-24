# STATE — 2026-09-24

Stack loads on 1.0.15; mod list frozen (§3) but Quick Stack Store
(#46), WEC (#124): Gale install on both PCs, then `sync-configs.ps1 -Pull`. Logs/dumps off
(#66): `-Push` both PCs. Launched clean (0 exceptions);
84 clones, unlaunched since. Object drop targets come from `rate-model.py objects`;
camped 321 kills/hr (§7). Deploy needs `validate-configs.py` on the PC.
Herb run: crops -> `Potion_Meadbase` -> potion, both at `opalchemy` 2, 17
Alchemy gates (WIRSL 331), `herbwife`, 5 Harvest contracts (Farming XP x0.5 by hand, #152).
`check-alchemy-balance.py` 8/8.
GoldOre (Petrified Tissue): not sold to `gem_trader`, rewards paid as coin (#64).
Oaths: all 8 biomes — 40 quests, 8 keys, 8 waystone tiers, `oath_supplies`,
8 capes, all logged. `chapel_oath` is back and rebuilt on bone cost.
15 boss/elite uniques drop as EpicLoot Legendaries (beam + highlight, 1 signature
effect, §10); Troll verified, bosses unseen. Magic: 2-stars 4%,
map chests: coins + gem 2/3 or magic item 1/3, shard rarity by biome (#107), enchanting table off (#108), forge rings off. Uniques lose one-per-player.
Quests live: 79 story (57 new), 43 hunts, skip fees (§11).
Balance review 2026-09-24, benchmarked on local data 09-23: `scripts\sim-run.py` (`validate` 15/15), report
https://claude.ai/artifact/D1kS4fnF1uDbsSYZvYE9FJ; fixes in PRs #137-#140 (coins still ~405k held: bounties 116k, sinks).

## Needs a live world
All in-game checks: #156 (pinned; ModTest, two players, Gielheim).

## Gielheim (Doug plays and reports)
1. Create Gielheim on the host (panel world name, Sven deploys first): new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Claude places the KG NPCs (`gen-npcs.py --town`, open meadow by the sea; admin char only; `--builder off` after, §11).
2. After session one the AI reads `LogOutput.log` (WIRSL `Loaded: 331`).
3. Doug vetoes renames.

## First Gielheim sessions
- Sessions record themselves (`watch.py`; Sven: his Claude asks).
- Day one: craft, block and helm once each at skill 0. Bars near 50% expected;
  far higher means the §6 ladder is cheap.
- Kills/hr, one 30 min farm per class, via `gen-loot.py --marker` (its
  docstring has the loop); the number goes into `loot\classes.csv`.
- Actions/hr and segments per ore node, the same way, into `loot\objects.csv`.

Waiting on upstream: KG Marketplace stable 10.x.

## Server
Live 2026-09-22: GGServers 8 GiB, fresh `Dedicated`, configs = 55fa2cd via
`sync-server.ps1` (behind main), mods = `mods.tsv`. MWL live, host dumps off;
2.5 GiB boot, 4.0 GiB after a 30 min solo fly (§15). First join can time out:
rejoin (§15). Open: Doug in `adminlist.txt`,
clone-drop and `DropOnePerPlayer` checks with both players present.
