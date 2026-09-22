# STATE — 2026-09-22

Stack loads on 1.0.15; mod list frozen (§3). Launched clean (0 exceptions);
73 clones, unlaunched since. Config audit: unfixed KG Talk quotes (§11).
Untested in play: 12 bone-cost prayers (§11), spawn spacing (§12), hellbroths
and the herb run on Alchemy (§6, §11, §18), mage purses (§7), lore renames
(§7, §11), Wizardry `supplies` + cauldron off (§21), Halla's collection log
(§11), fishing wave (§6, §11, §18), Sailing hull gates, skilling pets + curios
(§7), trinket + hatchet gates (§6), 7 elite uniques + crystal chest +
riddle-stones (§7, §11), biome oaths + waystones (§11), hull keels + 7 OdinShip
recipes (§6, §7, §11, §18), handbook + DistancedUI (§7, §11).
`drop_that.drop_table.cfg` is generated now (`gen-objects.py`); the old weights
dropped Feathers at 100% on ten empty log tables.
Herb run: crops -> `Potion_Meadbase` (opcauldron) -> potion (opalchemy), 17
Alchemy gates (WIRSL 320), `herbwife`, 5 Harvest contracts.
`check-alchemy-balance.py` 7/7. Measure the opcauldron batch and grow time
first.
OathCapes unlogged: #10.
Quest pass STAGED: `staging\quest-passpply-quest-pass.ps1` (57 story quests,
43 hunts, skip fees, 6 reward edits; §11).

## Gielheim (Doug plays and reports)
1. **Throwaway world first** (~20 s in-world): extract location YAML. Review
   MWL density now; `genloc` cannot retrofit explored terrain (§13). Dumps and
   mod prefab names confirmed.
2. Create Gielheim locally: new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Place the KG NPCs from the §11 table.
3. After session one the AI reads `LogOutput.log` (WIRSL `Loaded: 320`).
4. Watch for in play: superiors spawning, EpicLoot map / bounty paying coins,
   bank + shop, Wizardry potions, mage spawns, boss purse + unique on the first
   kill, coin sinks and bounty rules (§10, §11). Prayers: chapel takes bones
   not coins; groups stack. Riddle-stone off a Greydwarf and a boss; caskets
   pay out. Fishing: bait refused below level, `TrollingFishing.yml` appears.
   Elite unique + key half (§16), Gullveig forge, chest roll eats the key.
   Collection log: Talk quest completes at its giver, found lit, missing grey.
   Hulls (§6, §7): Hammer category, keel off a boss, helm refused below level.
   Quests: hidden ones open on the key, Pet tames, Harvest counts. Doug vetoes
   renames.

## First Gielheim sessions
- Day one: craft, block and helm once each at skill 0. Bars near 50% expected;
  far higher means the §6 ladder is cheap.
- Kills/hr, one 30 min farm per class, via `gen-loot.py --marker` (its
  docstring has the loop); the number goes into `loot\classes.csv`.
- Actions/hr and segments per ore node, the same way, into `loot\objects.csv`.

Waiting on upstream: KG Marketplace stable 10.x.

## Server (later)
§15: profile export, host standup, `Use Marketplace Locally = false`,
clone-drop and `DropOnePerPlayer` checks with both players.
