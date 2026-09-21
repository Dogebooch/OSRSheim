# STATE — 2026-09-21

Stack loads on 1.0.15; mod list frozen (§3).
Config audit: unfixed KG Talk quotes + buff multipliers (§11).
Launched 2026-09-21 clean (WIRSL 303, 56 wackydb clones, 0 exceptions).
Untested in play: spawn spacing (§12), hellbroths on Alchemy (§6), mage purses
(§7), lore renames (§7, §11), Wizardry `supplies` + cauldron off (§21), Halla's
collection log (§11), fishing wave (§6, §11, §18), Sailing hull gates, trinket
+ hatchet gates (§6), 7 elite uniques + crystal chest (§7, §11), hull keels +
7 OdinShip recipes (§6, §7, §11, §18), handbook + DistancedUI (§7, §11).
Validator clean.
Quest pass STAGED, not applied: `staging\quest-pass\apply-quest-pass.ps1`
(57 story quests, 43 hunts, skip fees, 6 reward edits; §11). Checker clean.

## Gielheim (Doug plays and reports)
1. **Throwaway world first** (~20 s in-world): extract location YAML. Review
   MWL density now; `genloc` cannot retrofit explored terrain (§13). Dumps,
   `*Mage_TW` and the 4 `Hellbroth_of_*` base names confirmed 2026-09-21;
   `_Charge` variants not yet.
2. Create Gielheim locally: new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Place the KG NPCs from the §11 table.
3. After session one the AI reads `LogOutput.log` for Drop That / WIRSL
   (`Loaded: 303`) / Spawn That warnings.
4. Watch for in play: superiors spawning, EpicLoot Haldor / map / bounty
   paying coins, bank deposit + shop buy, wandering troll, Wizardry potions
   at the alchemy table, mage spawns, boss purse + unique on the first kill.
   Coin sinks: Seeress offerings after a boss kill, 900 s blessings, skip fee,
   maps (pure sink), supplies meads and food. Bounties (§10): empty until the biome boss dies, one at a time, x6 coins.
   Fishing: bait refused below level, fish sell, The Harbour Wager completes,
   `TrollingFishing.yml` appears. Elite unique + key half (wiring session, §16), Gullveig forge, chest roll eats
   the key. Collection log: Talk quest completes at its giver, found lit,
   missing grey. Hulls: OdinShip Hammer category, keel off a boss (12.5%)
   or The Dugout Wager, canoe recipe lists the keel, helm refused below level.
   Quests: hidden ones open on the key, Pet tames, Harvest counts. Names:
   Doug vetoes renames (§7, §11).

## First Gielheim sessions
- Day one: craft one item at Blacksmithing 0, block one hit at Blocking 0,
  helm the raft one minute (Sailing bar vs the §6 calc).
  Bars near 50% expected; far higher means the §6 ladder is cheap.
- Kills/hr, one 30 min farm per class (camped, roamer, elite, boss):
  `gen-loot.py --marker <Creature> <Item>`, stack size = kills, number into
  `loot\classes.csv`, `gen-loot.py`, `dropthat:reload`.

## Waiting on upstream
KG Marketplace stable 10.x.

## Server (later)
§15: profile export, host standup,
`Use Marketplace Locally = false`, clone-drop and `DropOnePerPlayer` checks
with both players present.
