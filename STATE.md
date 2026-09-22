# STATE — 2026-09-21

Stack loads on 1.0.15; mod list frozen (§3). Launched clean (WIRSL 303, 0
exceptions); 84 clones, unlaunched. Config audit: KG Talk quotes unfixed (§11).
Untested in play: bone-cost prayers and biome oaths (§11), spawn spacing (§12),
hellbroths and the trinket / hatchet gates (§6), mage purses and lore renames (§7),
Wizardry `supplies` + cauldron off (§21), collection log and handbook (§11), fishing
wave (§18), Sailing hull gates, skilling pets + curios (§7), elite uniques + crystal
chest + riddle-stones (§7), hull keels + OdinShip recipes (§7), DistancedUI (§11).
`drop_that.drop_table.cfg` is generated now (`gen-objects.py`); the old weights
dropped Feathers at 100% on ten empty log tables. Next push needs `-Push`.
Biome oaths live in config (§11): 40 quests over 8 biomes, 8 keys, sworn stores,
`chapel_oath`, 8 capes. Needs `set-waystone.py` coords + 9 NPCs.
Quest pass STAGED: `staging\quest-passpply-quest-pass.ps1` (57 story quests,
43 hunts, skip fees; §11).

## Gielheim (Doug plays and reports)
1. **Throwaway world first** (~20 s in-world): extract location YAML. Review MWL
   density now; `genloc` cannot retrofit explored terrain (§13). `_Charge`
   hellbroth names still unconfirmed.
2. Create Gielheim locally: new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Place the KG NPCs from the §11 table and read
   `pos` at the 9 waystone spots (rules in the teleporter cfg).
3. After session one the AI reads `LogOutput.log` for Drop That / WIRSL / Spawn
   That warnings.
4. Watch for in play: superiors spawning, EpicLoot map / bounty paying coins,
   bank deposit + shop buy, wandering troll, Wizardry potions, mage spawns,
   boss purse + unique on the first kill.
   Coin sinks (§11). Prayers: bones not coins; groups stack. Bounties (§10).
   Riddle-stone off a Greydwarf and a boss; caskets pay out.
   Fishing: bait refused below level, fish sell, `TrollingFishing.yml` appears.
   Elite unique + key half (§16), Gullveig forge, chest roll eats the key.
   Collection log: Talk completes at its giver, found lit. Hulls (§6, §7): Hammer
   category, keel off a boss, helm refused below level.
   Quests: hidden ones open on the key, Pet tames, Harvest counts. Oaths: the seal
   needs all four, the key survives relog, locked replies render red, the fee is
   spent. Names: Doug vetoes renames (§7, §11).

## First Gielheim sessions
- Day one: craft, block and helm once each at skill 0. Bars near 50% expected;
  far higher means the §6 ladder is cheap.
- Kills/hr per class and actions/hr per ore node via `gen-loot.py --marker` (its
  docstring has the loop), into `loot\classes.csv` and `loot\objects.csv`.

Waiting on upstream: KG Marketplace stable 10.x.

## Server (later)
§15: profile export, host standup, `Use Marketplace Locally = false`, clone-drop
and `DropOnePerPlayer` checks with both players.
