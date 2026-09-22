# STATE — 2026-09-21

Stack loads on 1.0.15; mod list frozen (§3).
Config audit: KG Talk quotes + buff multipliers unfixed (§11).
Launched 2026-09-21 clean (WIRSL 303, 0 exceptions); 59 clones authored.
Untested in play: spawn spacing (§12), hellbroths and the trinket / hatchet
gates (§6), mage purses and lore renames (§7), Wizardry `supplies` + cauldron
off (§21), collection log and handbook (§11), fishing wave (§18), hull keels +
OdinShip recipes and Sailing gates (§7), elite uniques + chest (§7).
Biome oaths live in config (§11): 15 quests, 3 keys, waystones, sworn stores,
`chapel_oath`, 3 capes. Needs `pos` coordinates + 4 NPCs placed.
Validator: oath configs clean; 9 errors belong to a parallel session (loot
cfgs, collection log, 6 `log_osrs_*` rows whose clones do not exist yet).
Quest pass STAGED, not applied: `staging\quest-pass\apply-quest-pass.ps1`
(57 story quests, 43 hunts, skip fees; §11). Checker clean.

## Gielheim (Doug plays and reports)
1. **Throwaway world first** (~20 s in-world): extract location YAML. Review
   MWL density now; `genloc` cannot retrofit explored terrain (§13).
   `_Charge` hellbroth variants still unconfirmed.
2. Create Gielheim locally: new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Place the KG NPCs from the §11 table and
   read `pos` at each waystone.
3. After session one the AI reads `LogOutput.log` for Drop That / WIRSL /
   Spawn That warnings.
4. Watch for in play: superiors spawning, EpicLoot map / bounty paying coins,
   bank deposit + shop buy, wandering troll, Wizardry potions, mage spawns,
   boss purse + unique on the first kill.
   Coin sinks: offerings, blessings, skip fee, maps, food, waystone fee.
   Bounties (§10): empty until the biome boss dies, one at a time, x6 coins.
   Fishing: bait refused below level, fish sell, `TrollingFishing.yml` appears.
   Elite unique + key half (§16), Gullveig forge, chest roll eats the key.
   Collection log: Talk completes at its giver, found lit.
   Hulls: OdinShip Hammer category, keel off a boss (12.5%), helm refused below
   level. Quests: hidden ones open on the key, Pet tames, Harvest counts.
   Oaths: seal fires only with all four done, key survives relog, locked
   replies render red, fee leaves the purse. Names: Doug vetoes renames.

## First Gielheim sessions
- Day one: craft at Blacksmithing 0, block a hit at Blocking 0, helm the raft
  a minute. Bars near 50% expected; far higher means the §6 ladder is cheap.
- Kills/hr, one 30 min farm per class (camped, roamer, elite, boss):
  `gen-loot.py --marker <Creature> <Item>`, stack size = kills, number into
  `loot\classes.csv`, `gen-loot.py`, `dropthat:reload`.

## Waiting on upstream
KG Marketplace stable 10.x.

## Server (later)
§15: profile export, host standup, `Use Marketplace Locally = false`,
clone-drop and `DropOnePerPlayer` checks with both players present.
