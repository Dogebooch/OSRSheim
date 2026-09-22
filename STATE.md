# STATE — 2026-09-21

Stack loads on 1.0.15; mod list frozen (§3).
Config audit: unfixed KG Talk quotes + buff multipliers (§11).
Launched 2026-09-21 clean (0 exceptions).
Untested in play: spawn spacing (§12), hellbroths on Alchemy (§6), mage purses
(§7), lore renames (§7, §11), Wizardry `supplies` + cauldron off (§21), Halla's
collection log (§11), fishing wave (§6, §11, §18), Sailing hull gates, trinket
+ hatchet gates (§6), herb run (§6, §11, §18), 7 elite uniques + crystal chest (§7, §11), hull keels +
7 OdinShip recipes (§6, §7, §11, §18), handbook + DistancedUI (§7, §11).
BLOCKER: a concurrent worktree owns the profile - 177 files ahead (17 clones,
`oath_keeper`, `oath_supplies`, `waystone`). Do not `-Push`: merge the branches
in git, regenerate, push once (`post-build-check.py --repo`). The validator's 6
errors are all that branch.
Herb run in `config\`, unpushed: crops -> `Potion_Meadbase` (opcauldron) ->
potion (opalchemy), 17 Alchemy gates (WIRSL 320), `herbwife`, 5 Harvest
contracts. `check-alchemy-balance.py` 7/7. Measure the opcauldron batch and
grow time first.
Quest pass STAGED, not applied: `staging\quest-pass\apply-quest-pass.ps1`
(57 story quests, 43 hunts, skip fees, 6 reward edits; §11). Checker clean.

## Gielheim (Doug plays and reports)
1. **Throwaway world first** (~20 s in-world): extract location YAML. Review
   MWL density now; `genloc` cannot retrofit explored terrain (§13). Dumps and mod prefab names confirmed.
2. Create Gielheim locally: new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Place the KG NPCs from the §11 table.
3. After session one the AI reads `LogOutput.log` (WIRSL `Loaded: 320`).
4. Watch for in play: superiors spawning, EpicLoot map / bounty paying coins,
   bank + shop, Wizardry potions at the alchemy table, boss purse + unique on
   the first kill, coin sinks and bounty rules (§10, §11). Fishing: bait
   refused below level, `TrollingFishing.yml` appears. Elite unique + key half
   (§16), Gullveig forge, chest roll eats the key. Collection log: Talk quest
   completes at its giver, found lit, missing grey. Hulls: OdinShip Hammer
   category, keel off a boss (12.5%), helm refused below level. Quests: hidden
   ones open on the key, Pet tames, Harvest counts. Doug vetoes renames.

## First Gielheim sessions
- Day one: craft at Blacksmithing 0, block at Blocking 0, helm the raft a
  minute (Sailing bar vs the §6 calc). Near 50% expected; far higher = cheap.
- Kills/hr, one 30 min farm per class (camped, roamer, elite, boss):
  `gen-loot.py --marker <Creature> <Item>`, stack size = kills, number into
  `loot\classes.csv`, `gen-loot.py`, `dropthat:reload`.

## Waiting on upstream
KG Marketplace stable 10.x.

## Server (later)
§15: profile export, host standup,
`Use Marketplace Locally = false`, clone-drop and `DropOnePerPlayer` checks
with both players present.
