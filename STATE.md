# STATE — 2026-09-23

Stack loads on 1.0.15; mod list frozen (§3). Launched clean (0 exceptions);
84 clones, unlaunched since. Object drop targets come from `rate-model.py objects`;
camped class 321 kills/hr (§7). Deploy needs `validate-configs.py` on the PC.
Herb run: crops -> `Potion_Meadbase` (opcauldron) -> potion (opalchemy), 17
Alchemy gates (WIRSL 326), `herbwife`, 5 Harvest contracts.
`check-alchemy-balance.py` 7/7.
GoldOre (Petrified Tissue): not sold to `gem_trader`, rewards paid as coin (#64).
Oaths: all 8 biomes — 40 quests, 8 keys, 8 waystone tiers, `oath_supplies`,
8 capes, all logged. `chapel_oath` is back and rebuilt on bone cost.
15 boss/elite uniques drop as EpicLoot Legendaries (beam + highlight, 1 signature
effect, §10); Troll verified, bosses unseen. Uniques lose one-per-player.
Quest pass STAGED: `staging\quest-pass\apply-quest-pass.ps1` (57 story quests,
43 hunts, skip fees, 6 reward edits; §11); it writes repo `config\`.

## Needs a live world (issues carry the checklists)
#19 herb run — measure the opcauldron batch and the crop grow time FIRST, they
decide the whole Alchemy ladder · #21 biome oaths, which need
Sigrun + 9 waystones placed (Hammer templates) and `pos` at each (rules in the teleporter cfg;
`set-waystone.py` fills them in) · #22 riddle-stones · #23 collection log ·
#9 handbook · #42 superiors (`MaxSpawned 10`, 3%): do they appear in a BF night ·
#83 weapon XP per hit (one nest run) · #66 perf A/B: Exploration skill
0 vs 100 · #41 `Skill_EXP: Farming` hits the Smoothbrain skill.
Kills/hr for roamer/elite/boss still guesses (#70).
Still unseen and unticketed: spawn spacing (§12), mage purses and lore renames
(§7, §11), Wizardry `supplies` + cauldron off (§21), fishing wave (§18),
trinket + hatchet gates (§6), crystal chest (§7), boss drops (§7),
Sailing gates (§6, §7), DistancedUI (§11).

## Gielheim (Doug plays and reports)
1. **Throwaway world first** (~20 s in-world): extract location YAML. Review
   MWL density now; `genloc` cannot retrofit explored terrain (§13). Commit
   `..._LocationConfigs.yml` first; decide `MWL_TreeTowers1` / `MWL_MistTower2` (null loot, §13).
2. Create Gielheim locally: new character, death penalty Casual (§15), launch
   via `scripts\launch-modded.ps1`. Place the KG NPCs with the Hammer (16 templates, §11).
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
Live 2026-09-22: GGServers 8 GiB, fresh `Dedicated`, configs = 55fa2cd via
`sync-server.ps1` (behind main), mods = `mods.tsv`. MWL live, host dumps off;
2.5 GiB boot, 4.0 GiB after a 30 min solo fly (§15). First join can time out:
rejoin (§15). Open: `Use Marketplace Locally = false`, Doug in `adminlist.txt`,
clone-drop and `DropOnePerPlayer` checks with both players present.
