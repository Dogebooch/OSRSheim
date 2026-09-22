# STATE — 2026-09-22

Stack loads on 1.0.15; mod list frozen (§3). Launched clean (0 exceptions);
73 clones, unlaunched since. Config audit: unfixed KG Talk quotes (§11).
`drop_that.drop_table.cfg` is generated now (`gen-objects.py`); the old weights
dropped Feathers at 100% on ten empty log tables.
Herb run: crops -> `Potion_Meadbase` (opcauldron) -> potion (opalchemy), 17
Alchemy gates (WIRSL 320), `herbwife`, 5 Harvest contracts.
`check-alchemy-balance.py` 7/7.
Oaths: 15 quests, 3 keys, waystones, `oath_supplies`, 3 capes. `chapel_oath`
dropped in the merge: #24. OathCapes 5 of 8 uncommitted, unlogged: #10.
Quest pass STAGED: `staging\quest-pass\apply-quest-pass.ps1` (57 story quests,
43 hunts, skip fees, 6 reward edits; §11).

## Needs a live world (issues carry the checklists)
#19 herb run — measure the opcauldron batch and the crop grow time FIRST, they
decide the whole Alchemy ladder · #20 bone prayers · #21 biome oaths, incl.
placing 4 NPCs and reading `pos` at each waystone · #22 riddle-stones ·
#23 collection log · #14 object drop rates · #9 handbook.
Still unseen and unticketed: spawn spacing (§12), mage purses and lore renames
(§7, §11), Wizardry `supplies` + cauldron off (§21), fishing wave (§18),
trinket + hatchet gates (§6), 7 elite uniques + crystal chest (§7), hull keels
+ 7 OdinShip recipes and Sailing gates (§6, §7), DistancedUI (§11).

## Gielheim (Doug plays and reports)
1. **Throwaway world first** (~20 s in-world): extract location YAML. Review
   MWL density now; `genloc` cannot retrofit explored terrain (§13).
2. Create Gielheim locally: new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Place the KG NPCs from the §11 table.
3. After session one the AI reads `LogOutput.log` (WIRSL `Loaded: 320`).
4. Doug vetoes renames.

## First Gielheim sessions
- Day one: craft, block and helm once each at skill 0. Bars near 50% expected;
  far higher means the §6 ladder is cheap.
- Kills/hr, one 30 min farm per class, via `gen-loot.py --marker` (its
  docstring has the loop); the number goes into `loot\classes.csv`.
- Actions/hr and segments per ore node, the same way, into `loot\objects.csv`.

Waiting on upstream: KG Marketplace stable 10.x.

## Server (later)
§15: profile export, host standup, `Use Marketplace Locally = false`,
clone-drop and `DropOnePerPlayer` checks with both players present.
