# STATE — 2026-09-22

Stack loads on 1.0.15; mod list frozen (§3). Launched clean (0 exceptions);
84 clones, unlaunched since. Config audit: unfixed KG Talk quotes (§11).
`drop_that.drop_table.cfg` is generated now (`gen-objects.py`); the old weights
dropped Feathers at 100% on ten empty log tables.
Herb run: crops -> `Potion_Meadbase` (opcauldron) -> potion (opalchemy), 17
Alchemy gates (WIRSL 326), `herbwife`, 5 Harvest contracts.
`check-alchemy-balance.py` 7/7.
Oaths: all 8 biomes — 40 quests, 8 keys, 8 waystone tiers, `oath_supplies`,
8 capes, all logged. `chapel_oath` is back and rebuilt on bone cost.
Quest pass STAGED: `staging\quest-pass\apply-quest-pass.ps1` (57 story quests,
43 hunts, skip fees, 6 reward edits; §11).

## Needs a live world (issues carry the checklists)
#19 herb run — measure the opcauldron batch and the crop grow time FIRST, they
decide the whole Alchemy ladder · #20 bone prayers · #21 biome oaths, which need
9 NPCs placed and `pos` at 9 waystone spots (rules in the teleporter cfg;
`set-waystone.py` fills them in) · #22 riddle-stones · #23 collection log ·
#14 object drop rates · #9 handbook.
Still unseen and unticketed: spawn spacing (§12), mage purses and lore renames
(§7, §11), Wizardry `supplies` + cauldron off (§21), fishing wave (§18),
trinket + hatchet gates (§6), crystal chest (§7), boss drops (§7),
Sailing gates (§6, §7), DistancedUI (§11).
Loot rebalance (§7: lists at creature class, coin curve, nest class) not on the host yet.

## Gielheim (Doug plays and reports)
1. **Throwaway world first** (~20 s in-world): extract location YAML. Review
   MWL density now; `genloc` cannot retrofit explored terrain (§13).
2. Create Gielheim locally: new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Place the KG NPCs from the §11 table.
3. After session one the AI reads `LogOutput.log` (WIRSL `Loaded: 326`).
4. Doug vetoes renames.

## First Gielheim sessions
- Day one: craft, block and helm once each at skill 0. Bars near 50% expected;
  far higher means the §6 ladder is cheap.
- Kills/hr, one 30 min farm per class, via `gen-loot.py --marker` (its
  docstring has the loop); the number goes into `loot\classes.csv`.
- Actions/hr and segments per ore node, the same way, into `loot\objects.csv`.

Waiting on upstream: KG Marketplace stable 10.x.

## Server
Live 2026-09-22: GGServers 8 GiB, fresh `Dedicated`, configs = main via
`sync-server.ps1`, mods = `mods.tsv`. MWL live, 2.5 GiB boot, host dumps off
(§15). Open: `Use Marketplace Locally = false`, Doug in `adminlist.txt`,
clone-drop and `DropOnePerPlayer` checks with both players present.
