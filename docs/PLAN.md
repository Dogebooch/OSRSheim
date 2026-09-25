# PLAN — high-view review fixes (review 2026-09-24)

Baseline: main a981367 (= d7a9003 configs). No finding fixed since the review. Nothing below is applied.
Sources: review items re-checked line by line; changes in Appendices A-D (exact file:line, old -> new).
Sim: `python scripts/sim-run.py run --out %TEMP%\...` (balanced, mixed, seed 1, 400 runs unless noted).

## 1. Verdicts

| ID | Verdict | Reason (CLAUDE.md) | PR |
|---|---|---|---|
| B1 tamed kills pay | do | biome pays like vanilla | 1 |
| B2 killing-blow credit | do: document in Ulfar/Hrafn help | boss trophies drop once per kill (not per player); no mod install (list frozen) | 1 |
| B3 waystone ModTest coords | do: code now, rows blanked at Gielheim `--town` | Gielheim pins must be Gielheim coords | 1 |
| B4 riddle-stone m_value | do: 0 (+ Burl, Geode) | rewards are not vendor coin | 1 |
| B5 Scythe gate | do: Farming 30 | gate on the item's own skill | 1 |
| B6 pets not bankable | do | bank holds every collectible pet | 1 |
| B7 troll purse keyed on biome | do: TemplateId | biome pays like vanilla | 1 |
| B8 510/511 CLLC stars | do: UseDefaultLevels; keep defeated_eikthyr | vanilla feel (stars were the overtune) | 1 |
| B9 trimmed cape names | do | names match base | 1 |
| B10 sim trains Farming/Alchemy from 0 h | do | rates from rate model/sim must be true | 2 |
| B11 Ashlands raid stone tier | do: row 224 -> T4; rows 225-226 kept (validator needs twin drops), lowered in E5 | boss-tier map | 1 |
| B12 TrophyHare page, TrophyKvastur | do | every collectible gets a row | 1 |
| B13 profile behind, mods.tsv | do at ship (step 4) | configs flow repo -> profile | ship |
| E1 boss re-kill purse | do | biome pays like vanilla | 2 |
| E2 Jotun core priced elite | do: class nest | biome pays like vanilla | 2 |
| E3 nests 2-3.5x | do | biome pays like vanilla | 2 |
| E4 coin surplus / raw-mat sales / contract coin | do | repeatables pay items; coins <= 200k | 2 |
| E5 raid stones 8% | do: 1-2% | caskets not flooded | 2 |
| E6 free tithes | do: Collect trophies | light grind, not login bonus | 2 |
| E7 bane stone tier | do | one tier above boss | 2 |
| E8 hunter rank per contract | do: weight by size | rank must reach 200 in-run | 2 |
| E9 one kill scores all quests | defer #156 | needs live world | — |
| E10 coins buy prayers | do: remove WitheredBone sales | coins must not buy power | 2 |
| E11 shop food completes tasks | do: unsold dishes | task = the skill, not the shop | 2 |
| E12 damage scroll 500c | do: remove from shop | coins must not buy damage | 2 |
| E13a-c price ladder | do | tier order | 2 |
| E13d superior 40c flat | reject | E4 gem pay covers it | — |
| E13e herb seed > pay | fixed by E4c | — | — |
| E13f herb skip fee | reject | Harvest counts own plots, nothing to skip | — |
| G1 Blacksmithing DN 70 unreachable | do: DN gates 65 | run ~375 h to 70 | 3 |
| G2 Blocking 33 median | defer #156 (measure blocks/kill); fallback in App. C | input is a guess | — |
| G3 rares after gate | do: gates from sim | rare rule 1 | 3 |
| G4 late weapon ladder | do: Ashlands 55, DN 65 all families | gate reached in its biome | 3 |
| G5 skills max in-run | do: Alchemy, Farming, Sailing, Exploration factors | run ~375 h to 70 | 3 |
| G6 elite oath asks | do: 11 asks lowered | asks reachable in biome order | 3 |
| G7 bolt gates | do: 10/20/25/30 | bolts match crossbow tier | 3 |
| G8 AxeBlackMetal 40 | do: 35 | tool before its biome | 3 |
| G9 Smoothbrain numbers | do: Cooking 1.0, extra upgrade off, Building x1.5 | gates unlock things, not numbers | 3 |
| G10 unmodelled gates | do: 3 gate fixes + sim additions | rare rule 1, tier order | 3 |
| I1 unique effects roll on normal items | do: weight 0; re-theme glaive, warblade | rare rule 2 | 4 |
| I2 cudgel/warblade damage | do | half a tier over drop biome | 4 |
| I3 Grands lost biome ingredient | do: Grand Healing Needle, Grand Spiritual Cloudberry | each tier its biome input | 4 |
| I4 Windrunner two twists | do: signature only | one thing per rare | 4 |
| I5 Amber torc +40 | do: +25 | small power | 4 |
| I6 Chain weight 0.1 | do: delete | vanilla material | 4 |
| I7 weight twists | do: revert | one twist | 4 |
| I8 OSRS names (crystal key) | do; names Doug decides | no OSRS names | 4 |
| I9 Queen's lash Spirit | do: 0 | one thing per rare | 4 |
| I10 Saga hood set membership | do + #156 | cosmetics give no power | 4 |
| Q1 locked quests visible | do: 17 HiddenAnyCondition; dedupe great_brain_robbery | board shows only what is open | 5 |
| S1 night superiors | reject | vanilla: night spawns leave at dawn | — |
| S2 CLLC per-player HP | defer #156 | two players | — |
| S3 defeated_frozenking_p3 | no action (in #156) | — | — |
| X1 duplicate loottables | reject | decompile: every table rolls | — |
| Stale docs/comments | do | docs match configs | 5 |

## Doug decides
| Item | Proposal |
|---|---|
| I8 renames | Crystal key -> Hoard key; halves -> Hoard key bow / bit; crystal chest -> the Gambler's hoard |

## 2. B10 sim fix and results

Change, `scripts\sim-run.py` `Run.farm()`:
- :801 `if hands_on <= 0:` -> `if hands_on <= 0 or idx_phase < 1:                  # Cultivator needs Bronze: farming from BlackForest`
- :812 `pl.add_xp('Alchemy', ...)` -> wrap: `if idx_phase >= BIOMES.index('Mountain'):  # Potion_Meadbase: opalchemy 2 + Turnip (post-Bonemass)`
- Stone factor: sim `stone = 3.0` stays = 1 + cfg 2 (check-alchemy-balance: additive). When G5 lands: `stone = 2.0`, gate `>= 60`.

| Metric | Before B10 | After B10 | After B10 + G5 (100 runs) | After all E* (40 runs, sim S1+S2) |
|---|---|---|---|---|
| Coins held at run end (median/player) | 245,147 | 245,278 | — | 189.5k (target <= 200k) |
| Farming @375 h | 95 | 94 | 86 (70 @252 h) | — |
| Alchemy @375 h | 100 (100 @321 h) | 100 (70 @261 h, 100 @372 h) | 81 (70 @320 h) | — |

Skill medians @375 h, after B10 (unchanged by it): Swords 69, Bows 60, ElementalMagic 34, Blocking 33, Blacksmithing 67, Mining 59, Lumberjacking 50, Cooking 68, Building 77, Sailing 98, Exploration 100, Fishing 60, Evasion 56, Foraging 21.

Uniques, P(drop before gate) before -> after B10 (gates unchanged; G3 resets them):

| Unique | Gate | Before | After |
|---|---|---|---|
| AbyssalBludgeon | Clubs 65 | 0.239 | 0.251 |
| AbyssalWhip | Swords 55 | 0.048 | 0.039 |
| BandosGodsword | Swords 45 | 0 | 0.001 |
| CrystalBow | Bows 55 | 0.571 | 0.575 |
| DragonAxe | Lumberjacking 18 | 0 | 0 |
| DragonBattleaxe | Axes 70 | 0.219 | 0.241 |
| DragonHalberd | Polearms 45 | 0.329 | 0.320 |
| DragonfireShield | Blocking 35 | 0.035 | 0.046 |
| GraniteMaul | Clubs 35 | 0.721 | 0.752 |
| HillGiantClub | Clubs 18 | 0.233 | 0.230 |
| RuneScimitar | Swords 27 | 0.004 | 0 |
| ScytheOfVitur | Polearms 70 | 0.035 | 0.050 |

P_before_gate is unconditional (= P(drop by gate)); conditional-on-drop timing is the G3 basis (App. C).

## 3. Phases (one PR each, in order)

| PR | Items | Files | Commands | Pass |
|---|---|---|---|---|
| 1 Bugs before Gielheim | B1-B9, B11, B12 + validator rules (App. A) | gen-loot.py, update-superiors.py, gen-npcs.py, set-waystone.py, validate-configs.py, loot\drops.csv, loot\collection-log.csv, Item_OSRS_RiddleStoneT1-4/Burl/Geode.yml, OathCapePlainsHard/SwampHard.yml, WackyMole.ItemRequiresSkillLevel.yml, Bankers\osrsheim_bank.cfg, Dialogues\osrsheim_dialogues.cfg | `gen-loot.py`; `update-superiors.py`; `gen-npcs.py`; `gen-collection-log.py`; `gen-handbook.py` | common gates; `gen-loot.py --check` 0 diffs; 0 `[X.N]` loot entries without `ConditionNotCreatureStates = Tamed`; `gen-collection-log.py --audit` 0 |
| 2 Sim + economy | B10, sim S1-S7 (App. B), E1-E8, E10-E13c | sim-run.py, reference\sim-profiles.csv, loot\drops.csv, loot\creatures.csv, Traders\osrsheim_traders.cfg, Quests\osrsheim_quests_{slayer,story,free,oaths,skilling}.cfg, research\loot.md | `gen-loot.py`; `gen-handbook.py`; `sim-run.py validate`; `sim-run.py run` | common gates; coins held at run end <= 200k; hunter rank 200 reached before 375 h; nest mixes <= 1.15x biome target; boss re-kill 0c/hr |
| 3 Gating | G1, G3-G10, G5 Alchemy/Farming (App. C) | WackyMole.ItemRequiresSkillLevel.yml, potionsplus.cfg:30, farming.cfg:68, sailing.cfg:301, exploration.cfg:62, cooking.cfg, blacksmithing.cfg:72, building.cfg:30, Quests\osrsheim_quests_oaths.cfg, sim-run.py (read factors from cfg), research\gating.md | `sim-run.py run` | common gates; Alchemy 70 @300-340 h, 75-85 @375 h; Farming <= 90 @375 h; Sailing, Exploration 70-80 @375 h; every G3 unique P(drop before gate | drop) >= 0.5; Blacksmithing median >= 65 @375 h |
| 4 Items/uniques | I1-I10 (App. D) | EpicLoot magiceffects.json, legendaries.json, shardstones.json, validate-configs.py, Item_OSRS_*.yml, SE_OSRS_TorcAmber.yml, ItemConfig.yml, potionsplus.cfg, collection-log.csv, dialogues/guide/free cfg, research\loot.md | `gen-collection-log.py`; `gen-handbook.py`; `check-alchemy-balance.py` | common gates; validator: every legendary signature effect SelectionWeight 0; no "crystal" in player-facing strings |
| 5 Quests + stale docs | Q1, stale lines (App. D) | quests_free.cfg, quests_story.cfg, WackyMole yml comments, update-superiors.py, research\gating.md, backlog.md, marketplace.md, slayer.cfg comment | `gen-handbook.py` | common gates; `grep -c HiddenAnyCondition` +17 |

Common gates (every PR):
- `python scripts/post-build-check.py --repo` = 0 errors.
- `python scripts/check-alchemy-balance.py` 8/8, 0 errors.
- `echo '{}' | python scripts/doc-guard.py` clean.
- Loot rules (validator): IDs >= 100 (lists 110+/120+), `ScaleByLevel = false`, vanilla drops never cleared, <= 100 items per entry, no `DropOnePerPlayer` on purses.
- `python scripts/sim-run.py validate` passes; sim run end coins <= 200k (from PR2 on).
- CRLF files (bank.cfg, oaths.cfg, potionsplus.cfg, research\*.md, collection-log.csv, SE_OSRS_TorcAmber.yml) edited as bytes, EOL kept.

## 4. Ship (after each merge)

| Step | Who |
|---|---|
| 1. Doug launches the profile once (Quick Stack Store loads), then `python scripts/gen-mods.py` (B13) | Doug + Claude |
| 2. `scripts\sync-configs.ps1 -Push` on Doug's PC | Claude, on Doug's PC |
| 3. Host deploy | Sven |
| 4. ModTest checks below, added to #156 | Doug + Sven |

#156 additions (ModTest, two players):

| Check | Expect |
|---|---|
| Boss killing-blow credit (B2, E1) | only the killer's `slayer_boss_*` / `oath_<b>_h1` advances; story boss quest credits both? |
| CLLC per-player HP (S2) | two players near a 0-star Greydwarf: 56 HP, not ~78 |
| Tamed kills (B1) | tamed Boar/Wolf/Lox kill: no Coins, gems, riddle-stones; no log/unknown-option warning |
| Waystones on Gielheim (B3) | after `gen-npcs.py --town`, every waystone line points at a Gielheim pin; biome rows re-measured |
| Saga hood set bonus (I10) | Gravebinder cloak + Troll set: no Troll bonus; Saga hood + 2 Ashlands medium: none |
| Grand Healing Tide (I3) | 95 HP total over 10 s |
| defeated_frozenking_p3 (S3) | `listkeys` after Kall |
| One kill, many quests (E9) | two accepted kill contracts on one kill: count both or one |
| Blocking XP (G2) | blocks per kill, 30 min Swamp session |
| Jotun kills/hr at a core (E2), fish/hr (E4), waystone trips/session (E4) | numbers into measured.csv |
| Buff-scroll duration (E12), new unique tooltips (I1), DarkBlue shard (I1) | as in App. D |
| 510 troll (B7, B8) | 600 HP, no stars; BF troll dragged to Meadows pays no purse |

## 5. Docs per phase

| PR | Doc | Change |
|---|---|---|
| 1 | STATE.md | "Waystones" line: code blanks biome rows at `--town`; B2 killing-blow rule under Quests |
| 1 | research\marketplace.md §11 | killing blow takes kill contracts (Quest_ProgressionHook.cs:266) |
| 2 | research\loot.md §7 | nest rule "spawner mix <= 1.15x target"; boss purse via story quest; raid stones 1-2%; tamed kills pay nothing |
| 2 | research\marketplace.md §11 | hunt contracts pay gems; hunter rank weighted; tithes collect trophies; :119 oath total 36,740 |
| 2 | research\wizardry.md:56 | DamageBuff scroll off the shop |
| 2 | STATE.md | Sim line: coins held -> new number |
| 3 | research\gating.md:9-10, :23-36, :57, :65-67 | Loaded 338; ladder table = sim numbers; bolts; uniques |
| 4 | research\loot.md:130, :185, :220, :227, crystal lines | App. D |
| 5 | backlog.md:23, slayer.cfg:413-414, yml comments, update-superiors.py | App. D stale table |
| each | STATE.md | edit the line the PR changes; <= 3.5 KB |
| last | docs\PLAN.md | delete |

---

## Appendix A: Bugs (B1-B9, B11-B13)
Worktree: herblore-roamer-design-decisions-0f1cbf @ d7a9003. Baseline: `post-build-check.py --repo` 0 errors, 1 warn (profile behind); `validate-configs.py --repo` 1 error (mods.tsv, B13).

| ID | Still true? (current file:line) | Exact change | Source + command | Pass check |
|---|---|---|---|---|
| B1 | YES. `ConditionNotCreatureStates` count: character_drop.cfg 0, _list.shared_tables.cfg 0, superiors 59 (key confirmed: superiors.cfg:16). Pet rewards: quests_story.cfg:70 Boar, :218 Wolf, :283 Lox. Drop That 3.1.5 DLL has the literal `ConditionNotCreatureStates`. | gen-loot.py `entry_text()` (:170-183): after `f'ChanceToDrop = {fmt(p)}', 'ScaleByLevel = false'` add `'ConditionNotCreatureStates = Tamed'` to the base `lines` list, so it is on every entry: creature and list (entry_text serves both; lists use the same item schema). 266 + 114 entries gain the line. KG kill-quest credit on tamed kills is not fixable in Drop That: accept it. | `python scripts\gen-loot.py --diff` then `python scripts\gen-loot.py`. Validator: validate-configs.py, Drop That loop (:184-210): error on any `[X.N]` entry section (not `.SpawnThat`) in any `drop_that.character_drop*.cfg` without `ConditionNotCreatureStates = Tamed`. | `gen-loot.py --check` 0 diffs; `post-build-check.py --repo` 0 errors; ModTest: LogOutput shows no Drop That unknown-option warning for list entries; kill a tamed boar: vanilla meat only, no Coins. |
| B2 | YES (config side). MarketPlace.cfg:76 `AllowKillQuestsInParty = true`; no Groups mod in plugins/. DLL cites (Quest_ProgressionHook.cs:266/:587) not re-read. Boss trophies are single drops: Debug before_changes `Eikthyr.0` TrophyEikthyr `DropOnePerPlayer = false` (gd_king.0, Bonemass.0 same), so trophy quests cannot credit both players. 24 boss Kill quests; only oath_<b>_h1 (8) gate anything (QuestFinished by the elite seals). | DECISION: keep kill credit; document it. Dialogues/osrsheim_dialogues.cfg (LF): :16 `[lumbridge_guide_help]` line: append ` A boss contract counts for whoever lands the killing blow. Two hunters need two summons.` :50 `[slayer_master_help]` line: append ` Only kills you land yourself count. On a boss the killing blow takes the contract.` No commas. Answers #156 "killer only?": yes. | Hand-edited. `sync-configs.ps1 -Push` after. | `post-build-check.py --repo` 0 errors; in game both lines render. |
| B3 | YES. npc-layout.csv:9 Banker meadows, :19-26 biome waystones hold ModTest coords -> teleports.cfg :36,:41,:47,:54,:62,:71,:81,:92 live. gen-npcs.py `town()` (:233-247) rewrites only `TOWN` keys; `teleports()` (:176-185) calls `waystone.render` only for `placed()` rows; set-waystone.py `render()` (:90-103) replaces, never comments. | Code now, data at the Gielheim `--town` run (blanking now breaks ModTest waystone tests; Gielheim does not exist yet). 1) set-waystone.py: add `def unset(key, text)`: every line whose `lstrip('# ')` starts `NODES[key] + ','` becomes `'# ' + line.lstrip('# ')`; return `'\n'.join(out) + '\n'`. 2) gen-npcs.py `teleports()`: for every `Waystone` row (node check kept): `placed(r)` -> `render` (as now), else `text = waystone.unset(r['node'], text)`. 3) gen-npcs.py `town()`: after the loop, `r.update(x='', y='', z='')` for every row not in `TOWN`; print the count (`N far rows blanked: measure on site with --set`). Kaupang stone line then stays commented until its y is measured (--town blanks y). | `python scripts\gen-npcs.py` (writes teleports cfg + builder). At Gielheim: `gen-npcs.py --town <x> <z> <heading>`, then `--set` per row. Validator: none new; `gen-npcs.py --check` (post-build-check step 5) then fails on a live teleport line whose layout row is blank. | Scratch run: copy layout, blank one waystone row, `gen-npcs.py --check` = stale; regenerate -> line commented; `set-waystone.py --show` lists it "not placed yet". |
| B4 | YES. Item_OSRS_RiddleStoneT1-4.yml have no `m_value`; items.json base m_value AncientGemstoneGreen 55, Orange 95, Purple 135, Black 175. | Insert `m_value: 0` after line 9 (`m_maxStackSize: 20`) in Item_OSRS_RiddleStoneT1.yml, T2, T3, T4 (all LF). Also Item_OSRS_Burl.yml and Item_OSRS_Geode.yml (inherit Amber 5; deviation, same class). `m_value: 0` key already used by 6 ring/torc ymls. | Hand-edited. Validator: validate-configs.py wackydb section (~:108-180): error when an Item_*.yml clone's base (reference/game-data/items.json) has m_value > 0 and the yml sets no `m_value`. Today trips exactly these 6. | `post-build-check.py --repo` 0 errors; ModTest: Haldor/Hildir sell list does not offer to buy a riddle-stone. |
| B5 | YES. WackyMole.ItemRequiresSkillLevel.yml:660-663 Scythe `Skill: Polearms`, `Level: 30`; items.json Scythe m_skillType 106 (Farming). Only mismatch of its kind in the file. | DECISION Farming 30. :662 `  - Skill: Polearms` -> `  - Skill: Farming` (Level 30 stays). Sim Farming: 42 end of Swamp, 52 end of Mountain (optimistic by B10, still > 30 at Plains entry 130 h). | Hand-edited. Validator: validate-configs.py section 3 WIRSL (:318): error when an entry's Skill is a vanilla weapon skill and the item's items.json m_skillType is not that skill (custom >= 100 or another weapon skill). | `post-build-check.py --repo` 0 errors; ModTest: Scythe equips at Farming 30, not at Polearms 30. |
| B6 | YES. Bankers/osrsheim_bank.cfg (CRLF) pets at :115-124: no OSRS_PetMining, OSRS_PetWoodcutting. | After :124 `OSRS_PetFarming` insert `OSRS_PetMining` and `OSRS_PetWoodcutting` (CRLF bytes). | Hand-edited. Validator: validate-configs.py after the banker loop (:412-415): error when a loot\collection-log.csv `Pets` prefab is not in `[bank]`. | `post-build-check.py --repo` 0 errors (also checks duplicate banker lines). |
| B7 | YES. superiors.cfg:846-878 Troll.200/201/210 keyed `ConditionBiomes = Meadows`, no SpawnThat subsection; update-superiors.py:119-122 `template=False`. | update-superiors.py: add `WANDERER = 'osrsheim_wanderer'`. Spawner loop: `if sid == 510: safety = f'TemplateId = {WANDERER}\n' + safety`. `entry(..., template=TEMPLATE)`: emit `[{creature}.{idx}.SpawnThat]\nConditionTemplateId = {template}` when `template` is set. Troll cond: drop `ConditionBiomes = Meadows\n` (keep key + Tamed); the three Troll entries pass `template=WANDERER`. | `python scripts\update-superiors.py` (writes both cfgs; .bak files already exist). Validator: validate-configs.py superiors block (:647-658): `WorldSpawner.510` templateid == `superior_spec['WANDERER']`; every `Troll.2xx` section has `[Troll.2xx.SpawnThat]` ConditionTemplateId == WANDERER. | `post-build-check.py --repo` 0 errors; ModTest: BF troll pulled into Meadows drops no Troll.200 purse. |
| B8 | YES. world_spawners_advanced.cfg 510 LevelMin/Max :204-205, 511 :226-227; no `[WorldSpawner.510/511.CreatureLevelAndLootControl]` (500-507 have it, e.g. :35-36). 510 `RequiredGlobalKey = defeated_eikthyr` (:209). | DECISION keep `defeated_eikthyr` for 510: frontier rule (key that opens BF), vanilla trolls meet post-Eikthyr gear in BF; the star bug was the real overtune. update-superiors.py spawner loop: `if sid in ROAMER_CHANCE and f'[WorldSpawner.{sid}.CreatureLevelAndLootControl]' not in block: block = block.rstrip() + f'\n[WorldSpawner.{sid}.CreatureLevelAndLootControl]\nUseDefaultLevels = true\n'`. The cfg is generated by update-superiors.py (loot.md:266): no hand edit. | `python scripts\update-superiors.py` (same run as B7). Validator: validate-configs.py loop over 500-511 (:647): error when `WorldSpawner.{sid}.CreatureLevelAndLootControl` is missing or `UseDefaultLevels` is not true. | `post-build-check.py --repo` 0 errors; ModTest Debug `spawn_that.world_spawners_loaded_configs.cfg` shows the 510/511 CLLC sections; a 510 troll has 600 HP, no stars. |
| B9 | YES. Item_OSRS_OathCapePlainsHard.yml:6 `Plainsworn cape (trimmed)` (base :6 `Heathsworn cape`); OathCapeSwampHard.yml:6 `Bogsworn cape (trimmed)` (base `Mirebound cape`). Also collection-log.csv:170, :172 and generated collection_log cfgs. | yml :6 -> `m_name: Heathsworn cape (trimmed)` / `m_name: Mirebound cape (trimmed)`. collection-log.csv:170 display -> `Mirebound cape (trimmed)`, :172 -> `Heathsworn cape (trimmed)`. | `python scripts\gen-collection-log.py` (rewrites Dialogues + Quests osrsheim_collection_log.cfg). Validator: validate-configs.py wackydb section: error when `OSRS_OathCape<X>Hard` m_name != `OSRS_OathCape<X>` m_name + ` (trimmed)`. (collection-log display == m_name already holds for all rows.) | `gen-collection-log.py --check` clean; grep Plainsworn/Bogsworn in config\ = 0. |
| B11 | YES. drops.csv:224 `Charred_Melee,OSRS_RiddleStoneT3,...,8,event`; Fader :160 T4. :225 Skeleton_NoArcher, :226 Draugr_sleeping raid rows: both `camped` in creatures.csv (:12, :20), never raid-spawned. | :224 -> `Charred_Melee,OSRS_RiddleStoneT4,1,1,8,event,`. Delete :225-226. (E5 rate change separate.) | `python scripts\gen-loot.py --diff`, then `python scripts\gen-loot.py` (same run as B1). | `gen-loot.py --check` 0 diffs; `post-build-check.py --repo` 0 errors. |
| B12 | YES. collection-log.csv:128 `Trophies: Deep North,TrophyHare` (spawners.json Hare m_biome 512 = Mistlands). TrophyKvastur: Debug before_changes `BogWitchKvastur.2` TrophyKvastur 100% (Swamp, Spawner_BogWitchKvastur_respawn_30); no log row. | :128 delete; insert `Trophies: Mistlands,TrophyHare,Hare trophy` after :116 (TrophyDvergr). Insert `Trophies: Swamp and Ocean,TrophyKvastur,Kvastur trophy` after :98 (TrophySerpent). | `python scripts\gen-collection-log.py`. Validator: gen-collection-log.py `collectibles()` (:120-135): add every `Trophy*` in reference/game-data/items.json except `{'TrophyDraugrFem', 'TrophyForestTroll'}` (no dropper in the dumps); today flags only TrophyKvastur. | `gen-collection-log.py --audit` 0 problems, `--check` clean. |
| B13 | YES. Profile lacks Quests/osrsheim_quests_skilling.cfg; profile slayer_skip greyling 10 vs repo 13; 67 files differ. `validate-configs.py --repo`: "no Loading [...] line matched ... Goldenrevolver-Quick_Stack_Store... mods.tsv is stale" (mods.tsv:8 plugin column empty: QSS never loaded since install). | Doug: launch the OSRSheim profile once (QSS gets a LogOutput Loading line), then Claude runs gen-mods.py. Then Push. Host: Sven after merge. | `python scripts\gen-mods.py`; `scripts\sync-configs.ps1 -Push` (Doug-approved step, ModTest only). | `validate-configs.py --repo` 0 errors; `post-build-check.py` (no --repo) no "repo differs from profile" warn. |

### Run order
1. B4, B5, B6, B9 yml/cfg, B2 dialogues, B11 + B12 csv rows (hand edits, preserve EOL: bank.cfg CRLF, rest LF).
2. gen-loot.py edit (B1) -> `gen-loot.py`.
3. update-superiors.py edits (B7, B8) -> `update-superiors.py`.
4. set-waystone.py + gen-npcs.py edits (B3) -> `gen-npcs.py` (no layout change now: output identical).
5. `gen-collection-log.py`.
6. Validator rules (B1, B4, B5, B6, B7, B8, B9, B12).
7. `post-build-check.py --repo` = 0 errors. B13 last (launch, gen-mods, Push).

### Open (not B-list)
- collection-log OSRS_ items not in `[bank]`: OSRS_Geode, OSRS_Burl, 6 keels, 6 jewellery, 4 bolts. Decide bankable or not.

## Appendix B: Economy (E1-E13) and sim additions
Evidence runs: scratch copies of the worktree, `python scripts/sim-run.py run --runs 40 --out <dir>` (balanced, mixed, seed 1).
"patched" = sim with S1+S2 below (PR2). Coin EV/hr: `python coin_ev.py <tree>` (scratch; drops.csv purse EV x spawner mix;
rate-model.py has no coin mode). Reference tree with every change applied + `gen-loot.py` + `gen-handbook.py` run:
(scratch, not kept) (its oaths.cfg lost CRLF: copy the edits, not the file). `validate-configs.py --repo` on it: only the pre-existing mods.tsv error.

| ID | Current file:line | Verdict + reason | Exact change | Command / evidence |
|---|---|---|---|---|
| E1 | drops.csv:127,132,137,142,147,152,157,161 (Coins 100%); :131,136,141,146,151,156,160,164 (.105 stone); story.cfg:79,106,171,310,375,449,532; free.cfg:101; slayer.cfg:530-670 | DO. Boss re-kill loop ~1,200c/hr + 8 T1/hr vs Meadows 150 (biome pays like vanilla). | Delete the 16 drops.csv rows. Story boss quests gain half the purse mean (per player; the drop was shared) + the tier stone (§E1). Repeats: `slayer_boss_*` unchanged (tier stone, cooldown 6, kc). Unique/pet/keel rows stay. Offerings: Bell 1200 -> 800 (offerings_7, offerings_8), HatefulBlood 1500 -> 1000 (offerings_8) so the unique chase costs what it did net of the old purse (Fader 34 x 2,400 = 82k, Kall 34 x 3,000 = 102k). Then `python scripts/gen-loot.py`, `python scripts/gen-handbook.py`. | E1 alone (unpatched sim): coin_end 245.2k -> 236.9k; purses 53.6k -> 42.5k; story 51.3k -> 54.6k; offerings 13.9k -> 11.2k; master caskets 10.5 -> 4.9/player. Loop after: 0c/hr, 1 T1 per 3 h per player. |
| E2 | creatures.csv:95-97 (was :111-113); drops.csv:111,112,115 | DO. Core-fed (BlackIce_Core 50 s, 6 near = 72/hr cap, game-data spawners.json) but priced as a x16 elite: ~1,903c/hr at 18.6 kills/hr, 4,706 at 46. | creatures.csv 95-97 class `elite` -> `nest`. drops.csv 111, 112, 115 `Coins,94,226,60` -> `Coins,94,226,20`. Giantsbane 1/256 x16 = 6.25% -> x1.74 = 0.68% per warrior kill (~4 h at 46/hr). `gen-loot.py`, `gen-handbook.py`. | coin_ev: EV/kill 102.3 -> 38.3 (incl. RareTableTier5 3% coins); at 46/hr 4,706 -> 1,762c/hr (1.10x DN 1,600); at 18.6/hr 712. #156: measure Jotun kills/hr at a core. |
| E3 | creatures.csv:9 (was :25); drops.csv:9,10,29,31 | DO. Nests pay 3.47x (BF) and 2.23x (Swamp) target; the camped rule must apply to the spawner mix. | creatures.csv 9 Greydwarf_Shaman `roamer` -> `nest`. drops.csv 9 Shaman `5,35,30` -> `5,35,5`; 10 Greydwarf_Elite `6,29,35` -> `6,29,5.7`; 29, 31 Draugr_Elite(_sleeping) `14,52,40` -> `14,52,8.5`. Basic purses unchanged (= target/321). loot.md rule "nest >= 1x" -> "nest purse: spawner mix <= 1.15 x target". `gen-loot.py`, `gen-handbook.py`. | coin_ev: GreydwarfNest 695 -> 230c/hr (1.15x of 200); DraugrPile 980 -> 504 (1.14x of 440). EV/kill Brute 6.12 -> 1.00, Shaman 6.00 -> 1.00, Draugr_Elite 13.2 -> 2.81. Sim E2+E3: coin_end 245.9k (sim camps no nests). |
| E4 | traders.cfg:27-37, 85-97; slayer.cfg hunt reward lines (§E4b); herb :420,428,437,446,455; sim-run.py:858-863, :780 | DO. Repeatables pay items (loot.md coin rule); raw-mat vendoring ~480c/hr vs BF 200. | Raw mats to token prices (§E4a). Hunt contracts: coins -> biome gem worth 1/3 of the old coin at Gullveig (Amber 8c no key/eikthyr, AmberPearl 20c gdking/bonemass, Ruby 40c dragon/goblinking, SilverNecklace 80c queen/fader), min 1, merged with existing gems (§E4b). Herb contracts: coins -> own seeds at herbwife value (§E4c). Skip fees (osrsheim_slayer_skip.cfg) stay in coins (the validator check goes inert: pay has no coins). | Patched sim, E4 alone: coin_end 243.3k -> 197.9k; hunt 37.3k -> 0, herb 22.3k -> 0, trader sales 31.1k -> 44.3k (gem pay 13.2k). Trees at Wood 50 -> 1: 1,600 wood/hr = 32c/hr (was 480). Needs S1, S2, S7. |
| E5 | drops.csv:217-226 | DO, % (Drop That has no per-raid cap). 8% = ~1.2-1.5 stones per raid. | 217-221 (T1/T2) chance 8 -> 2; 225 Skeleton_NoArcher, 226 Draugr_sleeping 8 -> 2 (kept: the validator needs the same drops as their display twin; deleting 225 errors); 222-223 (T3) 8 -> 1; 224 `Charred_Melee,OSRS_RiddleStoneT3,1,1,8,event,` -> `Charred_Melee,OSRS_RiddleStoneT4,1,1,1,event,` (B11 boss-tier map). `gen-loot.py`, `gen-handbook.py`. | ~16 kills/raid: 0.32 stones/raid (T1/T2), 0.16 (T3/T4). Sim skips event rows (sim-run.py:225): S6 to confirm <25% of each casket tier. |
| E6 | oaths.cfg:442-841 (8 tithes) | DO. Free Talk + AlwaysProgressServerTime = 8 stones every login. | Each `oath_<b>_tithe`: line +1 `Talk` -> `Collect`; line +4 `Sigrun the Oathkeeper` -> a trophy (none is a prayer cost or Seeress item): meadows 446 `TrophyBoar, 5`; blackforest 502 `TrophyGreydwarfBrute, 3`; swamp 558 `TrophyDraugr, 3`; mountain 614 `TrophyWolf, 5`; plains 670 `TrophyGoblin, 5`; mistlands 726 `TrophyTick, 3`; ashlands 782 `TrophyCharredMelee, 5`; deepnorth 838 `TrophyJotunWarrior, 2`. Line +3 desc -> "Bring Sigrun <n> <trophies> as the tithe." Reward and cooldown 6 unchanged. oaths.cfg is CRLF. | Needs S5. |
| E7 | slayer.cfg:544,562,580,598,616,634,652,670 | DO. Bane = one tier above the boss stone, cap T4. | 544 Eikthyr, 562 Elder T4 -> T2; 580 Bonemass, 598 Moder T4 -> T3; 616, 634, 652, 670 stay T4. | Patched all-changes sim: T4 stones 9.6 -> 5.1 per player, T3 19.1 -> 14.8 (E1+E7). |
| E8 | slayer.cfg reward lines (abomination :145, bonemaw :378, greydwarf :35) | DO. Rank must track effort, and today it never reaches the late gates. | `AddCustomValue: hunter_rank, 1` -> `max(1, round(old coin pay / 100))` on the 43 hunt contracts (1-10, §E4b). Elite and boss hunts stay 1. Gates 25/50/100/200 unchanged. | Patched sim, hours to rank 25/50/100/200: 53/126/298/never -> 54/96/134/185 (Swamp/Mountain/Plains/Mistlands start at 45/85/130/185 h); rank at run end 104.5 -> 383.5. Today Morgen/Jotun elite hunts never open. |
| E9 | Quests_DataTypes.cs:1049-1070 (decompile) | DEFER #156. Needs a live world. | None. The sim already credits every accepted contract from the same kills (shared `pl.kills`, sim-run.py:1040-1046). | Live: accept slayer_greydwarf + a story Greydwarf kill quest, kill 1, check both counters. |
| E10 | traders.cfg:135,140,146,155,164,173 (WitheredBone 150c); prayers.cfg:33 ward_grudge, :108 wisdom_mimir | DO. Coins bought +10% XP and 20% DR (prayers cost bones, never coins). | Delete `Coins, 150, WitheredBone, 1` from offerings_3..8 (6 lines). Bonemass summon bones drop at 12% from Draugr (~38/hr camped). Prayers unchanged. Optional validator rule: a buffer cost prefab must not be a trader result. | Sim prices WitheredBone at 0 -> Bonemass summon 0 coins (bones farmed). |
| E11 | skilling.cfg:96,105,114; oaths.cfg:428,587,643 (blocks :424, :583, :639) | DO. Shop food completes Cooking tasks (coins skip a skill task). | skilling 96 `CookedMeat, 20` -> `NeckTailGrilled, 20`; 105 `WolfMeatSkewer, 10` -> `WolfJerky, 10`; 114 `LoxPie, 10` -> `BloodPudding, 10`. oaths 428 `DeerStew, 10` -> `CarrotSoup, 10`; 587 `WolfMeatSkewer, 15` -> `Eyescream, 15`; 643 `LoxPie, 10` -> `BloodPudding, 10`. Titles and descs name the new dish. All unsold; prefabs in game-data items.json. | No coin effect. |
| E12 | traders.cfg:220,249,281,318,358 | DO, remove. Coins must not buy damage (gates unlock things, not numbers). | Delete `Coins, 500, ArcaneScroll_DamageBuff_TW, 1` from supplies_3..7. "Permanent" is unverified (wizardry.md:56 says terminal consumable): #156 check the other 3 scrolls' duration. | none |
| E13a | traders.cfg:234-235 ArrowObsidian = ArrowIron 160 | DO. Ladder by pierce (Iron 42, Obsidian 52, Poison/Frost 78). | ArrowObsidian 160 -> 200 (:235, 265, 301, 339); oath_supplies_4 :403 380 -> 465. | items.json damages |
| E13b | traders.cfg:303-304 ArrowCarapace = ArrowFrost 300 | DO. Carapace 72 pierce sits between Frost and Charred 82 (400c). | ArrowCarapace 300 -> 350 (:304, :342). | items.json |
| E13c | traders.cfg:81-82 TrophyBjorn 100 > TrophyMoose 60 | DO. Trophy price by biome tier. | :81 TrophyMoose 60 -> 120; :82 TrophyBjorn 100 -> 60 (= TrophyFrostTroll). | none |
| E13d | slayer_superior_* flat 40c (:89, 154, 210, 266, 313) | REJECT. Superseded by E4 gem pay; `creature, 1, 2` also counts CLLC's natural 1% two-stars (farmable at a nest), so no raise. | None beyond §E4b. | |
| E13e | herb seeds cost > herb pay | FIXED by E4c (pay = seeds at parity). | | |
| E13f | herb_* no skip fee (slayer.cfg:415-455) | REJECT. Harvest counts own plots; nothing to skip past. | none | |

### Sim additions, PR2 (scripts/sim-run.py)
| # | Change | Why |
|---|---|---|
| S1 | :1148 sort `W.contracts` by `coins + sum(n x W.prices['sell'][item])`, not `-q.coins` | item-paid contracts fall to file order; completions fell 2,154 -> 514 in an unpatched E4 run |
| S2 | :1060 skip fee from `QuestEvents\osrsheim_slayer_skip.cfg` (`RemoveItem, Coins, N`), not `q.coins / 3` | coin-less contracts show a 0 skip sink (the real fee stays) |
| S3 | `boss_kill()` extras (k >= 1): pay `slayer_boss_<boss>` items + `kc_<boss>` at most once per 6 game days (3 h); `boss_bane_<boss>` at kc 10 | repeat stones and banes unmodelled (contracts() skips bosses, :1084) |
| S4 | none: OFFERING cost already reads the Seeress price (WitheredBone 0 after E10 = bones farmed) | confirm only |
| S5 | tithes: Collect consumes N trophies from `pl.has`; refresh per session (AlwaysProgressServerTime), not per played hours (:957-958) | E6 |
| S6 | raids: new keys `rate.raids_per_hour`, `rate.kills_per_raid` (guess ~16); load `event` rows (:225); report stones by source | E5 <25%-of-tier check |
| S7 | raw-mat + fish sales: wood/stone/resin per chop/mine hour (rate-model trees/mining), hides/pelts per kill (vanilla-drops.csv), new `rate.fish_per_hour` (guess 30) x §E4a prices | E4; the sim sells only gems/curios/trophies (:858-863), fishing is XP only (:780) |
| S8 | `rule.trips_per_session` (guess 1) drives the 35k waystone sink (45% of sinks): measure (#156) | E4 |

Re-run needed: E1 (S3), E4 (S1, S2, S7), E5 (S6), E6 (S5), E8 (the timing above used S1+S2). E2/E3/E7/E10-E13: no sim-visible risk; E2 needs the #156 core measurement.

Combined (all E changes, patched sim): coin_end 243.3k -> 189.5k (target <= 200k); creature purses 53.1k -> 41.4k; story 51.1k -> 54.6k;
trader sales 31.1k -> 44.3k; offerings 13.9k -> 9.7k; caskets opened simple/cryptic/elaborate/master 278/131/19.7/9.4 -> 273/125/14.4/4.9.

Docs to edit after merge: loot.md §7 (nest rule; "Bosses 200-400c ..." line; riddle-stone table "Boss .105" row -> story quest; raid 8% line),
marketplace.md §11 (offerings "~1.25x the mean boss purse" rule; hunt/herb contract pay; tithe; buff scrolls), wizardry.md:56 (4 scrolls -> 3), traders.cfg header :11 "~10x".

### §E1 story boss quests (Item line)
| File:line | Quest | Old | New |
|---|---|---|---|
| story.cfg:79 | demon_slayer (Eikthyr) | Coins 150, MeadHealthMinor 3 | Coins 300, MeadHealthMinor 3, OSRS_RiddleStoneT1 1 |
| story.cfg:106 | the_grand_tree (Elder) | Coins 300, SurtlingCore 5 | Coins 525, SurtlingCore 5, OSRS_RiddleStoneT1 1 |
| story.cfg:171 | priest_in_peril (Bonemass) | Coins 600, Iron 10 | Coins 900, Iron 10, OSRS_RiddleStoneT2 1 |
| free.cfg:101 | dragon_slayer (Moder) | Coins 1250, WolfPelt 5 | Coins 1625, WolfPelt 5, OSRS_RiddleStoneT2 1 |
| story.cfg:310 | legends_quest (Yagluth) | Coins 2000, BlackMetal 10 | Coins 2450, BlackMetal 10, OSRS_RiddleStoneT3 1 |
| story.cfg:375 | monkey_madness (Queen) | Coins 3000, Eitr 10 | Coins 3525, Eitr 10, OSRS_RiddleStoneT3 1 |
| story.cfg:449 | dragon_slayer_ii (Fader) | Coins 3000, FlametalNew 10 | Coins 3600, FlametalNew 10, OSRS_RiddleStoneT4 1 |
| story.cfg:532 | song_of_the_elves (Kall) | Coins 4300 | Coins 5050, OSRS_RiddleStoneT4 1 |

Format: `Item: Coins, N | Item: X, n | Item: OSRS_RiddleStoneTk, 1`. demon_slayer has no gate, so a missed accept is fixed by accepting and re-summoning.
Rejected alternative: Drop That `ConditionNotGlobalKeys` on the boss purse (key-set vs drop-roll order on a client-owned boss unverified; gen-loot has no notkey flag).
##156: a boss Kill quest credits both players in range.

### §E4a general_store sells (traders.cfg)
| Line | Old | New |
|---|---|---|
| 27 | Wood, 10, Coins, 3 | Wood, 50, Coins, 1 |
| 28 | Stone, 10, Coins, 2 | Stone, 50, Coins, 1 |
| 29 | Resin, 5, Coins, 2 | Resin, 20, Coins, 1 |
| 30 | Flint, 5, Coins, 2 | Flint, 20, Coins, 1 |
| 31 | Feathers, 5, Coins, 2 | Feathers, 20, Coins, 1 |
| 32 | LeatherScraps, 5, Coins, 3 | LeatherScraps, 20, Coins, 1 |
| 33 | BoneFragments, 10, Coins, 5 | BoneFragments, 20, Coins, 1 |
| 34 | DeerHide, 5, Coins, 10 | DeerHide, 10, Coins, 2 |
| 35 | TrollHide, 5, Coins, 40 | TrollHide, 5, Coins, 5 |
| 36 | WolfPelt, 5, Coins, 50 | WolfPelt, 5, Coins, 5 |
| 37 | LoxPelt, 2, Coins, 60 | LoxPelt, 5, Coins, 5 |
| 85 | FishRaw, 5, Coins, 5 | FishRaw, 10, Coins, 1 |
| 86-97 | Fish1 3, Fish2 3, Fish5 6, Fish6 10, Fish3 12, Fish8 12, Fish4_cave 15, Fish7 20, Fish12 30, Fish9 30, Fish11 40, Fish10 50 | 1, 1, 2, 3, 3, 3, 4, 5, 8, 8, 10, 12 |

Trades stay at 50 items or fewer. Fish come to ~20% of the biome target at a guessed 30 fish/hr (#156: measure fish/hr).

### §E4c herb contracts (slayer.cfg, Item line; Skill_EXP kept)
| Line | Quest | Old | New |
|---|---|---|---|
| 420 | herb_carrot | Coins 50, CarrotSeeds 3 | CarrotSeeds 18 |
| 428 | herb_turnip | Coins 65, TurnipSeeds 3 | TurnipSeeds 15 |
| 437 | herb_onion | Coins 90, CarrotSeeds 6 | OnionSeeds 12 |
| 446 | herb_barley | Coins 175, OnionSeeds 6 | OnionSeeds 21 |
| 455 | herb_flax | Coins 175, TurnipSeeds 6 | TurnipSeeds 36 |

The onion contract and the herbwife onion page share `defeated_dragon`, so no seed arrives ahead of its page.

### §E4b / E8 / E7 slayer.cfg lines (old -> new)
```
  17 slayer_greyling            Item: Coins, 40 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 2 | AddCustomValue: hunter_rank, 1
  25 slayer_boar                Item: Coins, 40 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 2 | AddCustomValue: hunter_rank, 1
  35 slayer_greydwarf           Item: Coins, 110 | Item: Amber, 1 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 6 | AddCustomValue: hunter_rank, 1
  44 slayer_skeleton            Item: Coins, 70 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 3 | AddCustomValue: hunter_rank, 1
  53 slayer_shaman              Item: Coins, 95 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 4 | AddCustomValue: hunter_rank, 1
  62 slayer_brute               Item: Coins, 60 | Item: Amber, 1 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 3 | AddCustomValue: hunter_rank, 1
  71 slayer_troll               Item: Coins, 90 | Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 4 | Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
  80 slayer_bjorn               Item: Coins, 90 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 4 | AddCustomValue: hunter_rank, 1
  89 slayer_superior_greydwarf  Item: Coins, 40 | AddCustomValue: hunter_rank, 1
                                -> Item: Amber, 2 | AddCustomValue: hunter_rank, 1
 100 slayer_draugr              Item: Coins, 205 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 3 | AddCustomValue: hunter_rank, 2
 109 slayer_blob                Item: Coins, 90 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 2 | AddCustomValue: hunter_rank, 1
 118 slayer_leech               Item: Coins, 45 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 1 | AddCustomValue: hunter_rank, 1
 127 slayer_surtling            Item: Coins, 55 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 1 | AddCustomValue: hunter_rank, 1
 136 slayer_wraith              Item: Coins, 160 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 3 | AddCustomValue: hunter_rank, 2
 145 slayer_abomination         Item: Coins, 50 | Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 1 | Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
 154 slayer_superior_draugr     Item: Coins, 40 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 1 | AddCustomValue: hunter_rank, 1
 165 slayer_wolf                Item: Coins, 325 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 5 | AddCustomValue: hunter_rank, 3
 174 slayer_fenring             Item: Coins, 185 | Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 3 | Item: Ruby, 1 | AddCustomValue: hunter_rank, 2
 183 slayer_drake               Item: Coins, 70 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 1 | AddCustomValue: hunter_rank, 1
 192 slayer_golem               Item: Coins, 190 | Item: Crystal, 2 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 3 | Item: Crystal, 2 | AddCustomValue: hunter_rank, 2
 201 slayer_ulv                 Item: Coins, 245 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 4 | AddCustomValue: hunter_rank, 2
 210 slayer_superior_wolf       Item: Coins, 40 | AddCustomValue: hunter_rank, 1
                                -> Item: AmberPearl, 1 | AddCustomValue: hunter_rank, 1
 221 slayer_fuling              Item: Coins, 800 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 7 | AddCustomValue: hunter_rank, 8
 230 slayer_lox                 Item: Coins, 80 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
 239 slayer_deathsquito         Item: Coins, 40 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
 248 slayer_fuling_shaman       Item: Coins, 260 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 2 | AddCustomValue: hunter_rank, 3
 257 slayer_fuling_brute        Item: Coins, 170 | Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 2 | AddCustomValue: hunter_rank, 2
 266 slayer_superior_fuling     Item: Coins, 40 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
 277 slayer_seeker              Item: Coins, 850 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 7 | AddCustomValue: hunter_rank, 8
 286 slayer_gjall               Item: Coins, 215 | Item: SilverNecklace, 1 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 2 | Item: SilverNecklace, 1 | AddCustomValue: hunter_rank, 2
 295 slayer_tick                Item: Coins, 75 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
 304 slayer_seeker_soldier      Item: Coins, 215 | Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 3 | AddCustomValue: hunter_rank, 2
 313 slayer_superior_seeker     Item: Coins, 40 | AddCustomValue: hunter_rank, 1
                                -> Item: Ruby, 1 | AddCustomValue: hunter_rank, 1
 324 slayer_charred             Item: Coins, 245 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 1 | AddCustomValue: hunter_rank, 2
 333 slayer_morgen              Item: Coins, 470 | Item: Ruby, 2 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 2 | Item: Ruby, 2 | AddCustomValue: hunter_rank, 5
 342 slayer_twitcher            Item: Coins, 195 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 1 | AddCustomValue: hunter_rank, 2
 351 slayer_charred_archer      Item: Coins, 120 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 1 | AddCustomValue: hunter_rank, 1
 360 slayer_volture             Item: Coins, 105 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 1 | AddCustomValue: hunter_rank, 1
 369 slayer_asksvin             Item: Coins, 390 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 2 | AddCustomValue: hunter_rank, 4
 378 slayer_bonemaw             Item: Coins, 155 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 1 | AddCustomValue: hunter_rank, 2
 389 slayer_jotun               Item: Coins, 950 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 4 | AddCustomValue: hunter_rank, 10
 398 slayer_jotun_witch         Item: Coins, 600 | Item: Ruby, 2 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 2 | Item: Ruby, 2 | AddCustomValue: hunter_rank, 6
 407 slayer_frozen_dead         Item: Coins, 480 | AddCustomValue: hunter_rank, 1
                                -> Item: SilverNecklace, 2 | AddCustomValue: hunter_rank, 5
 420 herb_carrot                Item: Coins, 50 | Item: CarrotSeeds, 3 | Skill_EXP: Farming, 20
                                -> Item: CarrotSeeds, 18 | Skill_EXP: Farming, 20
 428 herb_turnip                Item: Coins, 65 | Item: TurnipSeeds, 3 | Skill_EXP: Farming, 30
                                -> Item: TurnipSeeds, 15 | Skill_EXP: Farming, 30
 437 herb_onion                 Item: Coins, 90 | Item: CarrotSeeds, 6 | Skill_EXP: Farming, 45
                                -> Item: OnionSeeds, 12 | Skill_EXP: Farming, 45
 446 herb_barley                Item: Coins, 175 | Item: OnionSeeds, 6 | Skill_EXP: Farming, 75
                                -> Item: OnionSeeds, 21 | Skill_EXP: Farming, 75
 455 herb_flax                  Item: Coins, 175 | Item: TurnipSeeds, 6 | Skill_EXP: Farming, 75
                                -> Item: TurnipSeeds, 36 | Skill_EXP: Farming, 75
 544 boss_bane_eikthyr          Item: OSRS_RiddleStoneT4, 1
                                -> Item: OSRS_RiddleStoneT2, 1
 562 boss_bane_elder            Item: OSRS_RiddleStoneT4, 1
                                -> Item: OSRS_RiddleStoneT2, 1
 580 boss_bane_bonemass         Item: OSRS_RiddleStoneT4, 1
                                -> Item: OSRS_RiddleStoneT3, 1
 598 boss_bane_moder            Item: OSRS_RiddleStoneT4, 1
                                -> Item: OSRS_RiddleStoneT3, 1
```

## Appendix C: Gating (G1-G10)
Base: worktree HEAD d7a9003. yml = `config\WackyMole.ItemRequiresSkillLevel.yml`; oaths = `config\Marketplace\Configs\Quests\osrsheim_quests_oaths.cfg`. Line numbers = the `Level:` line (PrefabName line in brackets).

### Sim basis

| Run | Command |
|---|---|
| balanced | `python scripts/sim-run.py run --out %TEMP%\sim` (400 runs, seed 1) |
| fighter | `python scripts/sim-run.py run --profile fighter --out %TEMP%\simf` |
| unique timing | level of the family-main curve at each player's first drop (1000 runs; G10 sim addition `unique_timing` makes this permanent) |

Median level at phase end (balanced / fighter). Farming and Alchemy are pre-B10; see section 2.

| h | Swords | Bows | Elem | Blocking | Bsmith | Mining | LJ | Cooking | Building | Sailing | Explor | Fishing | Evasion | Foraging |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15 | 12/14 | 10/12 | 0/0 | 7/8 | 29/29 | 7/7 | 18/13 | 18/18 | 20/14 | 26/23 | 30/27 | 14/10 | 13/16 | 8/9 |
| 45 | 27.5/34 | 24/29 | 12/15 | 14/18 | 38/38 | 22/20 | 24/20 | 28/28 | 32/22 | 41/37 | 47/42 | 23/18 | 22/27 | 10/12 |
| 85 | 39/48 | 33/41 | 18/23 | 20/25 | 45/45 | 31/27 | 29/24 | 37/37 | 41.5/29 | 53/47 | 61/54 | 31/24 | 29/37 | 12/14 |
| 130 | 44/54 | 38/47 | 21/26 | 22/27 | 50/50 | 38/33 | 34/28 | 44/44 | 49.5/35 | 63/57 | 72/65 | 38/29 | 36/45 | 14/17 |
| 185 | 47/58 | 42/51 | 23/28 | 24/29 | 55/55 | 44/39 | 38/32 | 51/51 | 57/40 | 73/65 | 84/75 | 44/34 | 42/52 | 16/19 |
| 245 | 52/63 | 45/54 | 27/32 | 25/31 | 60/60 | 49/44 | 42/36 | 58/58 | 64/45 | 82/73 | 94/84 | 49/40 | 47/59 | 18/22 |
| 310 | 63/75 | 55/65 | 31/37 | 29/37 | 64/64 | 55/49 | 46/39 | 63/63 | 71/51 | 90/81 | 100/92 | 55/45 | 51/64 | 20/23 |
| 375 | 69/83 | 60/71 | 34/41 | 33/41 | 67/67 | 59/53 | 50/43 | 68/68 | 77/55 | 98/87 | 100/100 | 60/49 | 56/69 | 21/25 |

Clubs (10% share) balanced: 5/13/19/22/24/26/31/34. Biome start h: BF 15, Swamp 45, Mountain 85, Plains 130, Mistlands 185, Ashlands 245, DN 310.

### Verdicts

| G | Cited lines now | Verdict | Principle |
|---|---|---|---|
| G1 | blacksmithing.cfg:96 First Craft Bonus 125, :102 Threshold 5, :108 Factor 0.5, :116 gain 0.5; DN Bsmith 70 at yml:1591-1727, 2953, 2962 | do: DN gates 70 -> 65; cfg unchanged | gate times it: 65 reached ~330 h (20 h into DN); no bonus/factor pair fits 15..70 under the sim's flat crafts/biome (best fit 25/33/39/44/49/52/56); early invisible craft gates cost nothing |
| G2 | shields yml:311-1720; oaths:460 Blocking 35, :628 50, :740 60; sim-profiles.csv:86 blocks_per_kill 1.0 guess | defer #156 (measure blocks/kill); fallback below | numbers from measurement, not guesses |
| G3 | uniques yml:434, 450, 466, 1911, 1927, 3276, 3292, 3308, 3324, 3340, 3356, 3372 | do: table below | Rares rule 1 |
| G4 | Swords Ash 60 yml:909-981, DN 70 yml:1285-1330 | do: Ash 60 -> 55, DN 70 -> 65 (all weapon families) | each biome gears like vanilla: gate reached ~20 h into its biome |
| G5 | sailing.cfg:301 gain 0.5; exploration.cfg:62 gain 0.5 | do (Alchemy/Farming: see below) | ~375 h to 70; 70-100 optional |
| G6 | oaths:404-823 (32 SkillMore asks) | do: lower 11 asks (table) | elite oaths lit by run end in biome order |
| G7 | bolts yml:3475/3484/3493/3502 = 30/40/50/60; crossbows Ripper 20 yml:1134-1161, Gold 30 yml:1564-1582 | do: 10/20/25/30 | a gate unlocks a thing usable with the crossbow of its tier |
| G8 | AxeBlackMetal yml:52 (49) Lumberjacking 40 | do: 40 -> 35 | LJ 35 ~150 h (Plains); 40 = 204 h, after Mistlands start 185 h |
| G9 | cooking.cfg:18/24/30/36 = 1.3; blacksmithing.cfg:72 Extra Upgrade 80, :84 Durability 2; building.cfg:30 Health 3 | do (below) | gates unlock things, not bigger numbers |
| G10 | see G10 | do: sim spec + gate fixes | measure every gate |

### G1 Blacksmithing

| File:line | Item | Old | New |
|---|---|---|---|
| yml:1591,1600,1609,1618,1627,1636 | ArmorDeepNorth Medium/Heavy/Mage Chest+legs | 70 | 65 |
| yml:1645,1654,1663 | HelmetDNMage, HelmetDNHeavy, HelmetDNMediumHood | 70 | 65 |
| yml:1679,1695,1711,1727 | ShieldGold, ShieldGoldTower, ShieldGoldBuckler, ShieldRoots (Bsmith element) | 70 | 65 |
| yml:2953,2962 | TrinketBloodGoldHealth, TrinketBloodGoldStamina | 70 | 65 |

Ashlands 60 kept: reached 245 h = Ashlands start (felt). Sim models no Threshold/Factor falloff (sim-run.py:831); add it (G10) before touching :102/:108.

### G2 Blocking fallback (use only if #156 cannot measure)

Fallback = jujuz1.mods.skillgainmodifier.cfg:50 `Blocking = 0` -> `1` (replaces Global 0.5, x2 XP; median 33 -> 43 @375 h), then:

| File:line | Item | Old | New |
|---|---|---|---|
| yml:375 | ShieldSilver | 30 | 25 |
| yml:391, 409 | ShieldBlackmetal, ShieldBlackmetalTower | 40 | 30 |
| yml:875, 891 | ShieldCarapace, ShieldCarapaceBuckler | 50 | 30 |
| yml:1251, 1267 | ShieldFlametal, ShieldFlametalTower | 60 | 35 |
| yml:1672, 1688, 1704, 1720 | ShieldGold, GoldTower, GoldBuckler, ShieldRoots | 70 | 40 |
| oaths:460 | oath_blackforest Blocking | 35 | 30 |
| oaths:628 | oath_plains Blocking | 50 | 35 |
| oaths:740 | oath_ashlands Blocking | 60 | 40 |
| yml:450 | OSRS_DragonfireShield | 25 (G3) | 30 |

BF 15 / Swamp 20 shields kept. x2 curve at entry+20 h: 17 @35, 24 @65, 27 @105, 30 @150, 33 @205, 35 @265, 41 @330.

### G3 Uniques (gate = family-main median level at first drop, rounded up to 5)

Main curve = Swords curve (55% share); Bows main = x1.5 XP (STEP 1.5). P = share of drops landing below the gate on the main curve.

| Unique | Skill | Old | New | yml | Drop p50 h | Main lvl @drop p30/p50/p70 | P(below new gate) |
|---|---|---|---|---|---|---|---|
| OSRS_DragonAxe | Lumberjacking | 18 | 25 | 434 | 45 | 23/24/25 (own LJ) | 0.62 |
| OSRS_HillGiantClub | Clubs | 18 | 30 | 3276 | 36 | 21/25/33 | 0.66 |
| OSRS_RuneScimitar | Swords | 27 | 35 | 3292 | 64 | 31/34/37 | 0.55 |
| OSRS_GraniteMaul | Clubs | 35 | 45 | 3308 | 103 | 41/42/43 | 0.89 (40 = <0.3) |
| OSRS_DragonfireShield | Blocking | 35 | 25 | 450 | 130 | 22/22/23 (own) | >0.9 |
| OSRS_BandosGodsword | Swords | 45 | 50 | 466 | 185 | 47/47/48 | >0.9 |
| OSRS_DragonHalberd | Polearms | 45 | 50 | 3324 | 165 | 46/46/48 | 0.86 |
| OSRS_CrystalBow | Bows | 55 | 60 | 3340 | 213 | ~59 bow-main (own Bows 44) | ~0.6 |
| OSRS_AbyssalWhip | Swords | 55 | 55 (keep) | 1911 | 245 | 52/53/53 | >0.9 |
| OSRS_AbyssalBludgeon | Clubs | 65 | 65 (keep) | 3356 | 317 | 60/64/66 | 0.56 |
| OSRS_DragonBattleaxe | Axes | 70 | 70 (keep) | 3372 | 338 | 64/66/67 | >0.68 (65 = 0.32) |
| OSRS_ScytheOfVitur | Polearms | 70 | 70 (keep) | 1927 | 375 | 68/69/69 | 0.74 |

- Off-family players (Clubs at 10%: 12 @36 h, 21 @103 h, 31 @317 h) face a grind after the drop; that is the gate timing it.
- Fighter profile reaches gates before drops (Swords 58 @185 h); gates set for balanced.
- research/gating.md:65-67 uniques line: update to the new values; the #86 "gate half a tier above" rule becomes "gate = sim level at drop".

### G4 Weapon ladder (all families, same main curve)

| Tier | Old | New | Balanced reached | Lines |
|---|---|---|---|---|
| Mistlands | 50 | 50 (keep) | 214 h (29 h in) | - |
| Ashlands | 60 | 55 | ~262 h (17 h in) | Swords 909-981; Axes 990-1017; Clubs 1026-1053; Spears 1062-1089; Bows 1098-1125; staves 1833, 1842, 1851, 1861 |
| Deep North | 70 | 65 | ~330 h (20 h in) | Swords 1285-1330; Axes 1366-1384; Knives 1393-1420; Clubs 1429-1474; Polearms 1483-1501; Spears 1510-1528; Bows 1537-1555; Unarmed 1760-1778; staves 1871, 1881, 1891, 1900 |

Not changed: ShieldFlametal/Gold (G2), AxeGold (G10), uniques (G3), Bsmith (G1). research/gating.md:23-24 ladder -> 55/65; :26-36 table -> sim numbers:

| Biome | Gate | Balanced @entry | Fighter @entry |
|---|---|---|---|
| Black Forest | 15 | 12 | 14 |
| Swamp | 20 | 27.5 | 34 |
| Mountains | 30 | 39 | 48 |
| Plains | 40 | 44 | 54 |
| Mistlands | 50 | 47 | 58 |
| Ashlands | 55 | 52 | 63 |
| Deep North | 65 | 63 | 75 |

### G5 Exploration, Sailing, Alchemy, Farming
- Alchemy: potionsplus.cfg:30 `Philosophers Stone XP Gain Factor = 2` -> `1`; WIRSL yml:3165/3174/3183/3192 Alchemy `50` -> `60`.
- Farming: org.bepinex.plugins.farming.cfg:68 `Skill Experience Gain Factor = 0.5` -> `0.3`.
- Sim (after B10, 100 runs): Alchemy 70 @320 h, 81 @375 h; Farming 70 @252 h, 86 @375 h. sim-run.py reads these three values from the cfgs (stone = 1 + cfg; gate from yml).

| File:line | Key | Old | New | Result (scaled from sim XP) |
|---|---|---|---|---|
| org.bepinex.plugins.sailing.cfg:301 | Skill Experience Gain Factor | 0.5 | 0.25 | 74 @375 h; Longship full 30 ~45 h, Drakkar full 50 ~150 h |
| org.bepinex.plugins.exploration.cfg:62 | Skill Experience Gain Factor | 0.5 | 0.15 | 70 @~375 h; Cartography Read 40 ~118 h, Treasure 50 ~185 h; 100 needs ~82% of the map |

- Sim hardcodes both factors (sim-run.py:775, :779); it does not read these keys.
- Unverified: whether jujuz1 Global 0.5 also hits Smoothbrain skills. If yes, real rates are half the sim: use 0.5 (Sailing) and 0.3 (Exploration). Check in #156 (Exploration/Sailing level after a timed session).
- Philosopher's Stone: PhilosopherStonePurple/Green/Red/Blue Alchemy 50 at yml:3165, 3174, 3183, 3192 (PrefabName 3162, 3171, 3180, 3189); XP factor potionsplus.cfg:30.

### G6 Elite oath asks (target: median reaches the ask by Meadows 130 h, BF 185, Swamp 245, Mountain 275, Plains 310, Mistlands 330, Ashlands 350, DN 375)

| oaths line | Oath | Skill | Old | New | Old ask reached |
|---|---|---|---|---|---|
| 413 | meadows_h2 | Foraging | 30 | 15 | never |
| 478 | blackforest | Lumberjacking | 40 | 30 | 210 h |
| 487 | blackforest | Foraging | 40 | 20 | never |
| 534 | swamp | Lumberjacking | 45 | 35 | 292 h |
| 684 | mistlands | Evasion | 55 | 50 | 360 h |
| 693 | mistlands | Lumberjacking | 55 | 40 | never |
| 749 | ashlands | Mining | 60 | 55 | never |
| 758 | ashlands | Lumberjacking | 60 | 45 | never |
| 796 | deepnorth | Evasion | 65 | 55 | never |
| 805 | deepnorth | Lumberjacking | 65 | 50 | 375 h |
| 814 | deepnorth | Fishing | 70 | 60 | never |

- Blocking asks 460/628/740: G2. Foraging asks rest on `rate.forage_picks_per_roam_hour` 20 (guess); re-derive after #156.
- Farming 422/543/655 (30/40/55), Alchemy 702 (50): keep; with G5, Farming 40 @113 h, 55 @~170 h, Alchemy 50 @221 h, all before their oath targets.
- Exploration 711 (60): met at ~270 h with G5 0.15; keep.
- The other 17 asks are met before their target; keep.

### G7 Bolts

| yml | Item | Old | New | Matches |
|---|---|---|---|---|
| 3475 | OSRS_BoltAmber | 30 | 10 | CrossbowArbalest (ungated, Mistlands) |
| 3484 | OSRS_BoltPearl | 40 | 20 | CrossbowRipper 20 |
| 3493 | OSRS_BoltRuby | 50 | 25 | mid-Ashlands |
| 3502 | OSRS_BoltCrystal | 60 | 30 | CrossbowGold 30 |

Crossbows unmodelled; a crossbow main started at 185 h follows the main curve from 0: ~33 at +60 h, ~43 at +125 h. research/gating.md:57 -> new values.

### G8

yml:52 (PrefabName 49) AxeBlackMetal Lumberjacking 40 -> 35 (LJ 35 ~150 h).

### G9 Smoothbrain

| File:line | Key | Old | New |
|---|---|---|---|
| org.bepinex.plugins.cooking.cfg:18 | Health Increase Factor | 1.3 | 1.0 |
| cooking.cfg:24 | Stamina Increase Factor | 1.3 | 1.0 |
| cooking.cfg:30 | Regen Increase Factor | 1.3 | 1.0 |
| cooking.cfg:36 | Eitr Increase Factor | 1.3 | 1.0 |
| org.bepinex.plugins.blacksmithing.cfg:72 | Skill Level for Extra Upgrade Level | 80 | 0 (disabled) |
| org.bepinex.plugins.building.cfg:30 | Health Factor | 3 | 1.5 |

Kept: blacksmithing.cfg:84 Durability Factor 2 (convenience, not fight power); cooking Happy buff at 50 (:68, the unlock); building Free Build 50, Durability 30; sailing.cfg:295 Ship Health Factor 2. Combat index `x_cooking` column goes to 1.0.

### G10

Gate fixes:

| yml | Item | Old | New | Why |
|---|---|---|---|---|
| 758 | AxeJotunBane Lumberjacking | 50 | 40 | 50 = 365 h for a Mistlands axe; 40 = ~210 h |
| 1339, 1348, 1357 | AxeGold* Lumberjacking | 70 | 45 | LJ 50 @375 h; 45 = ~292 h (before DN) |
| 3247 | FishingBaitMistlands | 50 | 45 | 50 = ~250 h (after Mistlands) |
| 3256 | FishingBaitAshlands | 60 | 50 | 60 = 375 h |
| 3265 | FishingBaitDeepNorth | 70 | 55 | 70 never; 55 = ~310 h |

Check, no value yet: ShieldRoots (Blocking 70) stats vs ShieldSerpentscale; KnifeVoid (Knives 70, dmg 24) vs KnifeGold (150) tier; EpicLoot +skill effects count toward WIRSL (`GetSkillLevel` includes buffs) - test one gated item with a +skill magic item.

Sim spec (sim-run.py):

| Add | How |
|---|---|
| Per-player main weapon family | draw main from {Swords, Clubs, Axes, Polearms, Spears, Knives, Unarmed, Bows, Crossbows (from Mistlands), ElementalMagic, BloodMagic}; main 0.55, one secondary 0.25; gates of every family then measured |
| Output skills | levels/levels_ts/hours_to include Clubs, Polearms, Axes, Spears, Knives, Unarmed, Crossbows, BloodMagic, Ranching |
| unique_timing | use the unique's family as that player's main when computing P_before_gate; report conditional on drop (current column is unconditional) |
| Blacksmithing | model Threshold (:102) / Factor (:108) falloff per item; crafts scale per biome |
| Sailing/Exploration | read `Skill Experience Gain Factor` from cfg (now hardcoded 0.5 at :775, :779) |
| Wizardry shards | model shard drops (collection log Mage shards 0/5) and shard-gated rings/staves |
| Staves | mage-main profile: ElementalMagic main curve reaches 20/30/40/50 at 24/55/85/214 h (Wizardry 20/30/40/50 fine); at 10% share Elemental 20 = 105 h, 30 = 292 h |

## Appendix D: Items, quests, spawns, stale docs
Worktree: herblore-roamer-design-decisions-0f1cbf. Read-only pass; nothing edited.
EOL: LF = legendaries/magiceffects/shardstones.json, ItemConfig.yml, WIRSL yml, quests_*.cfg, dialogues/guide cfg, update-superiors.py, Item_OSRS_* (except oath capes/rings/torcs).
CRLF = potionsplus.cfg, research\*.md, loot\collection-log.csv, SE_OSRS_TorcAmber.yml. Edit bytes, keep EOL.
Gielheim not started (STATE): renames cost players nothing; Doug still vetoes.

### Verdicts

| # | Cited line now | Verdict | Reason (CLAUDE.md) |
|---|---|---|---|
| I1 | magiceffects.json weights at lines below; confirmed | do | Rare rule 2: signature effect must be on no other item |
| I1+ | shardstones.json:1630 DarkBlue Utility = Warmth (valueless, identical to Cinder cape) | do | Rare rule 2 (new finding) |
| I2 | AbyssalBludgeon.yml:9-13; BandosGodsword.yml:10-16 | do | Balance: half a tier above drop biome (#86) |
| I3 | potionsplus.cfg:1128, :1209 | do (2 Grands); reject :1296 :1384 :1691 :2948 :3284 | Design: each tier has its biome ingredient; pipeline A1 holds |
| I4 | GracefulCape.yml:9-12 | do | One twist per rare (signature effect only) |
| I5 | SE_OSRS_TorcAmber.yml:10 | do, 40 -> 25 | Balance: vanilla-scale carry (Megingjord 150 is a boss-tier item) |
| I6 | ItemConfig.yml:26-28 | do, delete | Balance: vanilla material weight (Chain 2.0 in items.json) |
| I7 | DragonAxe.yml:9, DraugrVisage.yml:7 | do, revert weight | One twist per rare |
| I8 | CrystalKey.yml:5, LoopHalfKey.yml:5-6, ToothHalfKey.yml:5-6, dialogues.cfg:95, quests_free.cfg:99 | do (names Doug-veto) | Don't copy OSRS names/quest text |
| I9 | AbyssalWhip.yml:6-8 flag, :19 Spirit 5 | do, Spirit 0 | Rare rule 2: its thing is the parry window; spirit is clone residue |
| I10 | Saga/Cloak/Crown ymls have no SE_SET_Equip | do (source-proven) + #156 check | Cosmetics give no power |
| Q1 | quests_free.cfg 16 blocks + story.cfg:48 lack tag | do | Consistency with story.cfg header ("Ulfar lists only what is open") |
| Q1b | great_brain_robbery free.cfg:189 = swan_song story.cfg:365 (Fish9 3, Fish12 3) | do | No duplicate asks |
| S1 | spawn_that.world_spawners_advanced.cfg:55 (501), :99 (503) | reject | Vanilla feel: night spawns leave at dawn |
| S2 | creaturelevelcontrol.cfg:33 (HP 40), :39 (DMG 4) | defer #156 | Needs two players |
| S3 | osrsheim_dialogues.cfg:121-128 | defer #156 (already listed: "After Kall, listkeys shows defeated_frozenking_p3") | no action |
| X1 | 17 duplicate Objects in loottables.json | reject | Decompile: AddLootTable appends to a List; RollLootTableInternal(IEnumerable) rolls every table. JotunWarrior L3 4% still rolls |

### I1 unique effects

EpicLoot decompile (Temp\el_decomp\EpicLoot\LootRoller.cs:1142-1154): GuaranteedMagicEffects use MagicItemEffectDefinitions.Get(type) + RollEffect with the legendary's Values; no weight, no requirement check. Random fill (:1160-1167) uses SelectionWeight. WeightedRandomCollection.Roll (`num2 >= num`) picks a 0-weight entry only when Random.value == 0 exactly. Weight 0 is safe; same pattern as AddCarryWeight.

magiceffects.json SelectionWeight -> 0:

| Effect | Unique | Line | Old |
|---|---|---|---|
| IncreaseTreeDrop | Rootcleaver | 893 | 10 |
| AddFireDamage | (was warblade; freed, leave 10) | 2201 | no change |
| ModifySprintStaminaUse | Windrunner cape | 3236 | 10 |
| LifeSteal | Morgen's cudgel | 3878 | 1 |
| ModifyAttackSpeed | Barrow blade | 4002 | 0.5 |
| Warmth | Cinder cape | 4083 | 0.2 |
| ExplosiveArrows | Gjall-gut bow | 4211 | 10 |
| ModifyStaggerDuration | Troll's knucklebone | 5265 | 3 |
| QuickLearner | Bog visage | 5314 | 5 |
| ReflectDamage | Drakeskull shield | 5498 | 10 |
| StaggerOnDamageTaken | Golemheart hammer | 5599 | 1 |
| ModifyDamageLowHealth | Giantsbane axe | 6032 | 10 |
| ModifyStaggerDamage | (was glaive; freed, leave 10) | 6641 | no change |
| ModifyParryWindow | Queen's lash | 6753 | 10 |
| Slow | Frost King's scythe | 6810 | 2 |
| Bloodlust | Warlord's glaive (new) | 3528 | 5 |
| Executioner | Yagluth's warblade (new) | 6400 | 0.2 |

Re-theme (two of four stagger uniques; knucklebone keeps stagger duration, Golemheart keeps stagger-when-hit + knockback):

| Unique | File:line | Old -> new |
|---|---|---|
| Yagluth's warblade | legendaries.json:489 | "A war-god's blade, still hot from the pyre." -> "A war-god's blade. What it wounds, it finishes." |
| | legendaries.json:499 | `"Type": "AddFireDamage"` -> `"Type": "Executioner"` |
| | legendaries.json:501-502 | MinValue/MaxValue 14 -> 200 (first hit on a foe under 20% HP +200%; Legendary roll 100-150, Mythic max 200) |
| Warlord's glaive | legendaries.json:638 | "...Every thrust knocks the wind out of its mark." -> "A fuling warlord's glaive. It drinks from the arm that swings it." |
| | legendaries.json:647-655 | `{ "Type": "ModifyStaggerDamage", "Values": {21,21,0} }` -> `{ "Type": "Bloodlust" }` (valueless, same shape as Cinder cape :542-544; attacks cost health, not stamina) |
| | DragonHalberd.yml:6 | m_description "...Heavier than the smith's pattern and it shows on the hit." -> "A fuling warlord's glaive. It drinks from the arm that swings it." |

Shard overlap (shardstones.json, map-chest shards): Yellow Utility Sprint (:235, max 7 vs 24), Grey Legs TreeDrop (:1223, max 3.5 vs 6), DarkPurple Chest Reflect (:1724, max 7 vs 14), Orange weapon Fire (:399/410/421; freed by re-theme): accept, magnitude 2-3x and different slot.
DarkBlue Utility Warmth is valueless, so identical to Cinder cape: shardstones.json:1630 `"EffectType": "Warmth"` -> `"EffectType": "AddFrostResistancePercentage"` (values 2-7 kept). Verify on ModTest (shard TypeEffects may ignore slot requirements; fallback: re-theme Cinder cape to AddElementalResistancePercentage 14).

Validator (validate-configs.py after :753):
```
for x in osrs_leg:
    for g in x.get("GuaranteedMagicEffects", []):
        if me.get(g["Type"], {}).get("SelectionWeight") != 0:
            err(f"EpicLoot {x['ID']}: signature effect {g['Type']} still rolls on magic items (SelectionWeight must be 0)")
```

Docs: loot.md:185 "`AddCarryWeight` and `CoinHoarder` weight 0" -> "`AddCarryWeight`, `CoinHoarder` and the 15 unique signature effects weight 0"; loot.md:220 `AddFireDamage 14` -> `Executioner 200`; :227 `ModifyStaggerDamage 21` -> `Bloodlust`.

### I2 damage

| Item | File:line | Old -> new | Effective |
|---|---|---|---|
| Morgen's cudgel | AbyssalBludgeon.yml:10, :13 | delete both `Custom_AttackSpeed: 1.1` | 135 x 1.13 = 152 (was ~168) |
| | :6 | "...It beats when swung, and swings quicker for it." -> "A morgen's heart bound into a club. It still beats when swung." | |
| | :14 | comment -> `# #86: blunt 135 -> 152, half a tier above Ashlands (Eldner 135 / Gold 170).` (unchanged text; speed gone) | |
| Yagluth's warblade | BandosGodsword.yml:10 | `Slash: 108` -> `Slash: 105` | 105 (Plains 95 / Mistwalker 115) |
| | :11-16 | delete Primary_Attack/Secondary_Attack blocks (speed 0.9, stagger 1.5) | |
| | :7 | "...Slow to swing, and nothing stands after it lands." -> "A war-god's blade. What it wounds, it finishes." | |
| | :2-3, :17-20 | trim header to `# Base SwordBlackmetal (dump: weight 0.8, Slash 95 (+6/lvl), stamina 14).`; delete VERIFY-BY-FEEL block (no custom speed left) | |

Docs: loot.md:130 `MaceEldner, dmg 1.13 (secondary 2.825), speed 1.1` -> `MaceEldner, dmg 1.13 (secondary 2.825)`.
Signature effect carries the power; stat twist one only (dump-verifiable, unlike Custom_AttackSpeed).

### I3 potions (potionsplus.cfg, CRLF)

Mod defaults (PotionsPlus.dll 4.3.4 PotionsSetup.cs:96-101; = 6f033c1): Grand Healing Tide Ooze2 Barley4 Needle2 Cloudberry6; Grand Spiritual Ooze4 Flax4 WolfFang2 Cloudberry6.
Current Grand Healing (Barley+Bloodbag) = Medium Healing (:2035 Turnip+Bloodbag); Grand Spiritual (Barley+Ooze) = Medium Spiritual (:2116 Turnip+Ooze). No Plains leg.

| Line | Old | New | Why |
|---|---|---|---|
| 1128 | `Potion_Meadbase:1,Barley:3,Bloodbag:4` | `Potion_Meadbase:1,Barley:3,Needle:2` | Plains mob drop, mod default |
| 1209 | `Potion_Meadbase:1,Barley:3,Ooze:4` | `Potion_Meadbase:1,Barley:3,Cloudberry:6` | Plains forage, mod default |
| 1296 | Flax + Cloudberry | keep | already Plains |
| 1384 | Flax + FreezeGland | keep | unique secondary, mod default |
| 1691 Thor's Fury | Flax + Tar | keep | Tar = Plains ingredient |
| 2948 Weapon Oil | Onion + Tar | keep | Tar present |
| 3284 Potion Base | Carrot + Turnip | keep | crops -> base pipeline (check A1); YmirRemains would gate the base |

Healing Effect 95 (:1079) = mod default, unchanged since 6f033c1. Decompile: sets SE_Stats.m_healthOverTime (total), m_healthOverTimeDuration 10, m_healthOverTimeInterval 1; tooltip "healing you for {power} health over {duration} seconds". 95 HP total, 9.5/tick. Not 950. No change.
After edit: `python scripts\check-alchemy-balance.py` (8/8 expected).

### I4 Windrunner cape (GracefulCape.yml, LF)

| Line | Old -> new |
|---|---|
| 8 | "Light as a rooftop breeze. Running and leaping cost less." -> "Light as a rooftop breeze. Running costs less." |
| 9 | `m_weight: 2` -> `m_weight: 4` (CapeDeerHide base) |
| 10-12 | delete `Moddifiers:` block (run -0.1, jump -0.1) |
Keep legendary ModifySprintStaminaUse 24 (legendaries.json:401 already "Running costs far less.").

### I5 Amber torc

| File:line | Old -> new |
|---|---|
| SE_OSRS_TorcAmber.yml:10 (CRLF) | `m_addMaxCarryWeight: 40` -> `25` |
| ServerInfos\osrsheim_guide.cfg:53 | `+40 carry weight` -> `+25 carry weight` |
| #156 §Jewellery | "Amber torc +40 carry" -> "+25"; "Megingjord + Amber torc: carry 490" -> "475" |

### I6 / I7

| File:line | Old -> new |
|---|---|
| ItemConfig.yml:26-29 | delete `Chain:` / `weight: 0.1` / `stack: 50` / blank |
| DragonAxe.yml:9 | `m_weight: 1.6` -> `m_weight: 2` |
| DraugrVisage.yml:7 | `m_weight: 2.25` -> `m_weight: 3` |

### I8 names (Doug-veto; prefab IDs unchanged)

| Now | Proposed |
|---|---|
| Crystal key | Hoard key |
| Loop half of a crystal key | Hoard key bow |
| Tooth half of a crystal key | Hoard key bit |
| crystal chest (Gambler, log page) | the Gambler's hoard |
| "earn the right to wear wolf armour" | dropped |

| File:line | Old -> new |
|---|---|
| Item_OSRS_CrystalKey.yml:5 | `m_name: Crystal key` -> `m_name: Hoard key` |
| Item_OSRS_LoopHalfKey.yml:5-6 | `Loop half of a crystal key` / "The bow of a crystal key. Useless without its tooth." -> `Hoard key bow` / "The ring end of a hoard key. Useless without its bit." |
| Item_OSRS_ToothHalfKey.yml:5-6 | `Tooth half of a crystal key` / "The bit of a crystal key. Useless without its loop." -> `Hoard key bit` / "The toothed end of a hoard key. Useless without its bow." |
| loot\collection-log.csv:17-19 (CRLF) | category `Crystal chest` -> `Gambler's hoard`; display -> the three names above |
| Dialogues\osrsheim_dialogues.cfg:95 | `Open the crystal chest` -> `Open the hoard` (Gambler id `crystal_chest` stays) |
| ServerInfos\osrsheim_guide.cfg:26 | `a crystal key` -> `a hoard key` |
| Quests\osrsheim_quests_free.cfg:99 | "Slay the dragon of the mountains and earn the right to wear wolf armour." -> "Slay the drake-mother of the mountains." |
| research\loot.md:122, :134-137, :163; research\gating.md:105 | "crystal chest/key" -> "Gambler's hoard / hoard key" |
| #156 §Riddle-stones | "`OSRS_CrystalKey`; "Open the crystal chest"" -> "`OSRS_CrystalKey` (Hoard key); "Open the hoard"" |
| comments only (optional): ItemConfig.yml:40, gamblers.cfg:15, traders.cfg:112, 3 key ymls :1 | "crystal" -> "hoard" |

Generated (never hand-edit): Quests/QuestProfiles/Dialogues `osrsheim_collection_log.cfg`, `Dialogues\osrsheim_handbook.cfg`.
Regen: `python scripts\gen-collection-log.py` ; `python scripts\gen-handbook.py` ; checks `gen-collection-log.py --check`, `gen-handbook.py --check`, `post-build-check.py --repo`.
Log page dialogue id becomes `collection_log_gambler_s_hoard` (gen-collection-log.py:55 slug strips the apostrophe).

### I9 Queen's lash (AbyssalWhip.yml, LF)

| Line | Old -> new |
|---|---|
| 6-8 | delete FLAGGED FOR DOUG block |
| 19 | `  Spirit: 5` -> `  Spirit: 0` |
Decision: 0 per level. Pure slash; signature = parry window 100.

### I10 set membership (wackydb SetData.cs:3405-3411: `SE_SET_Equip: EffectName: delete` nulls m_setName + m_setStatusEffect)

Append to each (bases may carry a set: CapeTrollHide = Troll set; Ashlands/DN medium hoods):
```
SE_SET_Equip:
  EffectName: delete
```
Files: Item_OSRS_SagaHood, SagaLastVerse, SagaCrown, SagaMantle, CloakGravebinder, CloakMistweave, CloakRimewalker, CloakWayfarer, CrownFeastday, CrownNine (.yml).
##156 add: "Gravebinder cloak + Troll helm/chest/legs: no Troll set bonus; Saga-friend's hood + 2 Ashlands medium pieces: no set bonus".

### Q1 HiddenAnyCondition

Header -> `[<id> = HiddenAnyCondition]`:

| File:line | id |
|---|---|
| quests_free.cfg:11 | cooks_assistant |
| :44 | witchs_potion |
| :69 | vampyre_slayer |
| :78 | goblin_diplomacy |
| :87 | black_knights_fortress |
| :96 | dragon_slayer |
| :105 | lost_city |
| :114 | desert_treasure |
| :129 | sea_slug |
| :137 | heroes_quest |
| :145 | pirates_treasure |
| :153 | fremennik_trials |
| :161 | rum_deal |
| :169 | cabin_fever |
| :177 | the_corsair_curse |
| :185 | great_brain_robbery |
| quests_story.cfg:48 | druidic_ritual |
Review listed 6; 17 untagged conditional quests exist (keel and skill-gated too). Profile lists ids only; unaffected.

Dedupe (keel quest changes; swan_song keeps the fish):

| quests_free.cfg:188-189 | Old -> new |
|---|---|
| 188 | "...Bring 3 anglerfish and 3 pufferfish." -> "The dvergr will seal a keel for those who bring mist timber and fish. Bring 10 yggdrasil wood and 5 pufferfish." |
| 189 | `Fish9, 3 \| Fish12, 3` -> `YggdrasilWood, 10 \| Fish12, 5` (both in items.json) |

### S1-S3, X1

| # | Action |
|---|---|
| S1 | none. 501 Skeleton, 503 Wolf stay night-only |
| S2 | #156 §Superiors add: "Two players near a 0-star Greydwarf: 56 HP (CLLC 40%), not ~78 (CLLC x vanilla)" |
| S3 | none (already in #156) |
| X1 | none; loot.md §10 add fact: "Duplicate `Object` tables all roll (AddLootTable appends)" |

### Stale docs / comments

| File:line | Old -> new | #156? |
|---|---|---|
| research\gating.md:9-10 (CRLF) | `Loaded:` / `331` -> `338` | also #156 §0 "WIRSL `Loaded: 331`" -> 338 |
| WIRSL yml:423-430 | Rule "gate each clone at its BASE item's existing gate" + UNGATED ON PURPOSE (capes, whip/scythe "no gate yet") -> `# #86: gate half a tier above the drop biome; second element GlobalKeyReq oath_<biome>. Capes: oath key only.` | no |
| WIRSL yml:1788-1793 | "Summoners are Blood... The three marked '?? UNVERIFIED'... TO VERIFY... authored Item_OSRS_*.yml" -> `# BloodMagic by game-data m_skillType (9 Elemental, 10 Blood).` (0 "?? UNVERIFIED" entries left) | no |
| WIRSL yml:1734-1738 (extra) | "SKILL NAME UNVERIFIED ... fails OPEN ... swap Unarmed -> Fists" -> `# UNARMED LADDER (Skills.SkillType Unarmed; WIRSL fails closed on a bad skill name, gating.md:86)` | no |
| WIRSL yml:2335-2336 | "Armor: EQUIP Blocking, CRAFT Blacksmithing, same split as every other set." -> "Armor, capes, circlets: CRAFT Blacksmithing, equip ungated." (all 45 `_TW` armor entries BlockEquip false) | no |
| #156 §Story | `cooks_assistant`: "+100c + 3 Bread" -> "+50c + 3 Bread (needs Cooking 10)" | yes |
| #156 §Story | `romeo_and_juliet`: "+25c" -> "+10c" | yes |
| #156 §Slayer | "`resetkeys`: only greyling, boar, greydwarf, skeleton, shaman, brute + herb contracts" -> "only slayer_greyling, slayer_boar, herb_carrot" (greydwarf/skeleton/shaman/brute need defeated_eikthyr) | yes |
| #156 §Slayer | `herb_carrot`: "daily cooldown" -> "2-day cooldown" | yes |
| research\backlog.md:23 (CRLF) | `waystone fee (25 / 50 / 100c)` -> `waystone fee (25-500c by oath tier)` | no |
| Quests\osrsheim_quests_slayer.cfg:413-414 | "Cooldown 1 = one day / (bare number = days), which is roughly one grow cycle per contract." -> "Cooldown 2 = two in-game days (bare number = days), about one grow cycle." | no |
| research\marketplace.md:119 (CRLF) | `36,380c` -> `36,740c` (40 base quests; elite tier 48 quests 8,800c) | no |
| scripts\update-superiors.py:1, :12, :50-52 | docstring "preserve originals beside each config" -> "git holds the originals"; delete `import shutil` and the 3 backup lines | no |
| config\*.bak-before-superior-balance (2 files, untracked, gitignored, sync-excluded) | delete locally (frozen pre-frontier) | no |

### #156 edits (gh issue edit 156)
§0 Loaded 331 -> 338 · §Jewellery +40 -> +25, 490 -> 475 · §Slayer resetkeys list, herb_carrot 2-day · §Story cooks_assistant 50c + Cooking 10, romeo_and_juliet 10c · §Riddle-stones hoard names · §Superiors S2 HP check · new: I10 set-bonus check, DarkBlue utility shard shows frost resistance, Warlord's glaive attacks drain health, Yagluth's warblade Executioner tooltip.

### Run after the edits
`python scripts\validate-configs.py --repo` · `python scripts\check-alchemy-balance.py` · `python scripts\gen-collection-log.py --check` · `python scripts\gen-handbook.py --check` · `python scripts\post-build-check.py --repo` · `echo '{}' | python scripts\doc-guard.py`
