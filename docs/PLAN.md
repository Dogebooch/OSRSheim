# Content additions: relics, dungeon sets, pets, saga belt, riddle journeys

Status 2026-09-25: S4 (gen-objects memo), step 1 (skill= flag, validator, sim method table + QuestEvents keys,
handbook tail, clone-count, key check, scroll exemption) and step 2 (pets) done. Next: S1-S3 in game
(spike kit: Claude installs, Doug plays), then steps 3-6. Delete this file when step 8 is done.

## Context
In play, OSRSheim's chase for key items is thin. Each player sees about 4 uniques across 375 h, and there is almost no mid-tier gear between currency drops and uniques. Five weapon families (Knives, Spears, Crossbows, Unarmed, Elemental magic) have no unique. Boss pets (flat 1/5,000) never drop. Riddle-stones are clicks, not activities.

Doug approved five additions. The goal is **end-user ready**: every item has a name, lore text, handbook and guide entries and a collection-log row, and passes every validator. The build must also be **ready for an official run-through**: a scripted ModTest checklist, then two players, then Gielheim.

Design principles that apply throughout (CLAUDE.md): Iron Gate test; rares rules 1-4; prefab names only from dumps or game-data; generated files never hand-edited; no new mods.

## Established facts (from exploration; decompiled Drop That 3.1.5)
- `ConditionKilledBySkillType` works and reads the killing hit's `HitData.m_skill`.
- Fire, poison and spirit damage are applied as DoT ticks with skill None, so a burn or poison kill never matches a skill condition.
- `ConditionKilledWithStatus(es)` is broken and `ConditionHitByEntityTypeRecently` is inverted. **Use neither.**
- A misspelled enum value makes the drop unconditional, so validation is mandatory.
- Drop That's `.EpicLoot` modifiers never apply to creature drops in this stack, so new rares are wackydb clones, not EpicLoot Legendaries.
- Chest tables are covered by Drop That's drop_table. They are shared with More World Locations ruins, which we accept.
- gen-objects caps an item at 1% of a table's picks, which gives at most 3.9-7.9% per chest. Its `miss()` takes about 100 s per big chest row.
- No clone keeps a set effect yet, and the `SE_SET_Equip` syntax is unverified.
- `m_swimStaminaModifier` is a plain item field.
- Every base prefab listed below exists in `reference/game-data/items.json`.

## Design

### A. Relic pattern
A relic is a gold-named Ancient material that drops from a condition. The player crafts the gear from relic + the tier's normal materials. WIRSL gates the craft. Upgrades never cost relics (`perLvl 0`).
- Gold name: `ammoType: 'Ancient|MagicCraftingMaterial'` + `m_itemType: Material`.
- No `one-per-player`: each player hunts their own relic.
- Both the relic and the gear get collection-log rows and are bankable.

**A1. Kill-method relics**, flag `skill=<SkillType>` in `loot/drops.csv`. No `dmg=` flag (simpler; frost and lightning can be added later).

| Family | Creature (biome) | Kill with | Relic | Crafted weapon (base) | Twist (one thing) | Gate |
|---|---|---|---|---|---|---|
| Knives | Fenring (Mountain) | Knives | Moonfang shard | Moonfang knife (KnifeSilver) | backstab bonus x1.5 | Knives, base gate +5 |
| Spears | Drake (Mountain) | Spears (thrown) | Drake-wing barb | Skyfall spear (SpearWolfFang) | throw damage x1.3 | Spears, base gate +5 |
| Crossbows | Seeker Soldier (Mistlands) | Crossbows | Chitin sight | Dvergr longshot (CrossbowArbalest) | reload x0.8 (key from base dump) | Crossbows, base gate +5 |
| Unarmed | Ulv (Mountain) | Unarmed | Ulv knuckle | Ulv-hide wraps (FistFenrirClaw) | stagger x1.5 | Unarmed, base gate +5 |
| ElementalMagic | Deathsquito (Plains) | ElementalMagic (frost/lightning) | Stormwing | Stormwing staff (StaffPlains_TW) | eitr cost x0.8 | ElementalMagic 45 |

- **Bonus rows** (plain items, `skill=` only): StoneGolem + Pickaxes → Crystal; Serpent + Spears → SerpentScale. Final list set in S4.
- **Chance** = 1 / (8 h × the class's kills/hr from `loot/classes.csv`), written as a literal percent.
- **Rule 1 check (S4):** the family skill after entering the biome plus 8 h of method XP must stay below the gate. If not, raise the gate or shorten the hours.
- Handbook text: "(knife kills only)". Staff text adds "frost or lightning killing blow".

**A2. Dungeon sets**: one relic per chest type, "<Dungeon> set relic". The player chooses which piece to craft, which avoids the 3-piece coupon grind.

| Chest | Biome | Stats cloned from | Set name | Set effect at 3 pieces |
|---|---|---|---|---|
| `TreasureChest_forestcrypt` | Black Forest | troll helm, chest, legs | Barrow-warden | Spears +15 |
| `TreasureChest_sunkencrypt` | Swamp | root | Mire-stalker | Knives +15 |
| `TreasureChest_mountaincave` | Mountain | fenris | Rimedelver | Pickaxes +15 |
| `TreasureChest_dvergrtown` | Mistlands | mage | Dvergr runner | Crossbows +15 |
| `TreasureChest_charredfortress` | Ashlands | Ask (AshlandsMedium) | Cinder-sworn | BloodMagic +15 (fallback Polearms if a vanilla set already gives it) |

- Every piece gets a unique `m_setName` and `m_setSize: 3`, so it never combines with vanilla pieces. Each set gets its own `SE_OSRS_Set*` (skill modifier, everything else zeroed).
- A set never boosts a skill a vanilla set already boosts. S2 confirms Sneak, Bows and Unarmed are taken.
- Crafting uses the Blacksmithing tier gate (the §6 armor split).
- Plains and Deep North have no dungeon set, by design.
- Rate target is about one full set per 8-10 dungeons of that type per player. It comes from S4's chest-per-dungeon count, within `MAX_SHARE`; if it can't be reached, report it rather than raise the cap.

### B. Pets (done 2026-09-25)
- Skilling pets (Mining, Woodcutting, Fishing, Farming): 0.1 expected per player-run each (Doug's rule
  p = 1/(10 x N)). Mining/Woodcutting via `rate-model.py` `PET_HOURS` (224 h / 210 h); Fishing 1 in 24,
  Farming 1 in 205 contract pools.
- Boss pets: 1 in 100 a kill, a grind (~100 summons, 12x the unique's rarity; ~3% a boss a run by chance).
  Doug's flat 0.1-a-run rule made them 1 in 30 (4x the unique), too easy to farm.
- `DropOnePerPlayer` (decompiled): one roll per kill; a hit drops one per player online, so a player's odds are the
  row's chance, not doubled.
- Sim: about 0.65 pets per player-run (skilling 0.4 + boss 0.24); `sim-run.py run` flags skilling drift > 25%.

### C. Saga belt (quest-key gear)
- **Chain:** "The Drowned Saga", 6 quests on Ulfar the Guide:
  1. Intro Talk.
  2. Catch fish (Meadows).
  3. Collect leech parts (Swamp).
  4. Kill Serpents (Ocean).
  5. Collect Chitin (Ocean).
  6. Collect Tar (Plains), with `SkillMore Swim 20`.
- Steps chain through `HiddenOtherQuestCondition`.
- The last quest's QuestEvent runs `AddPlayerKey, saga_selkie`.
- **Item:** Selkie belt, a BeltStrength clone with `m_swimStaminaModifier -0.5`, `SE_Equip` deleted (no carry weight) and a workbench recipe. It uses its own WIRSL element: `GlobalKeyReq: saga_selkie`, BlockCraft and BlockEquip both true (each player does the saga).

### D. Riddle journeys
- T3 and T4 stones stop opening caskets directly. The Gambler reply "Read the stone" opens a route gambler: cost 1 stone, prize one of 4 cairn scrolls. The scroll's description is the riddle text.
- **8 cairn NPCs**, each with a unique name and template, placed near waystones so waystone fees become a coin sink:
  - T3: Black Forest, Swamp, Mountain, Plains.
  - T4: Plains, Mistlands, Ashlands, Deep North.
- Each cairn's dialogue has a reply per scroll it accepts, conditioned on `HasItem`. The reply opens `OpenUI Gambler cairn_<x>_t<n>`, which costs that scroll and pays either another cairn's scroll or the casket (casket 2 of 6 slots: mean 3 hops, about 9% take 6+).
- **Caskets** (2 clones) become the cost of `riddle_elaborate` and `riddle_master`. Existing prizes stay, plus one journey-exclusive cosmetic per tier.
- Scrolls are exempt from the collection log (`OSRS_Scroll*`); caskets and the cosmetics get rows.
- Journeys add travel time in the sim. Placement: ModTest placements are thrown away; Gielheim needs 8 on-site admin placements after the world exists.

## S4 results (2026-09-25)
- gen-objects: bitmask memo, output byte-identical, a chest solve < 1 s (was ~100 s).
- Max per-chest chance at the 1% share cap: forestcrypt 3.9%, sunkencrypt 5.6%, mountaincave 6.6%, dvergrtown 6.0%, charredfortress 7.9%.
- Chests per dungeon: not in the dumps (rooms vary per instance). Guess until measured: BF crypt 2-4, sunken crypt 3-5. Measure on Gielheim (STATE watch).
- A1 rule 1 (model, hits/kill guessed): 8 h of method hunting overshoots the base+5 gates (Knives 43, Spears 49, Unarmed 47 at 8 h).
  Decision: 5 h mean hunt; gates Knives 40, Spears 40, Unarmed 40, Crossbows 25, ElementalMagic 45. Re-check with rate-model combat() in step 3.
- Seeker Soldier is `SeekerBrute` (elite, 5/hr): the crossbow relic moves to `Seeker` (roamer).

## Implementation sequence
Spikes S1-S4 run before any shipped data changes. B can start alongside S2 and S3.

| # | Step | Files | Done when |
|---|---|---|---|
| S1 | Drop That `skill=` spike on ModTest: a hand-written cfg with Boar + Knives, Unarmed, a frost-staff kill, a fire-staff burn kill, one misspelled enum | ModTest profile only | Correct drops; wrong weapon and burn kills give none; the misspelled enum always drops. Record in `research/loot.md` §7 |
| S2 | wackydb spike: one 3-piece set clone + SE, the belt, one gold relic | test ymls on ModTest | Set bonus only with 3 clone pieces; swim stamina halves; relic shows a gold name. Record `SE_SET_Equip` syntax and vanilla set skills in `research/gating.md` §8 |
| S3 | Marketplace spike: QuestEvent `AddPlayerKey saga_test` + WIRSL `GlobalKeyReq`; a `HasItem` reply that opens a Gambler test profile | test cfgs | Item locked, then unlocked after the quest; reply hidden without the scroll; gambler takes it |
| S4 ✓ | Numbers: memoize `miss()` in `scripts/gen-objects.py`; count chests per dungeon (location dumps / `count-world.py`); rate-model rule-1 timing (A1); dungeons-per-set (A2) | `gen-objects.py`, `rate-model.py` | gen-objects under 10 s with output unchanged; tables fix the A1 gates, A1 chances and A2 rates |
| 1 ✓ (set/SE checks + chest handbook section move to step 4) | Tooling (no data changes) | see list below | Regenerating everything is byte-identical; a bad-enum fixture fails |
| 2 ✓ | B pets | `loot/drops.csv`, `loot/objects.csv`, `Quests/osrsheim_quests_skilling.cfg`, `reference/sim-profiles.csv` | Sim: about 1.2 pets per player-run, P(≥1) ≈ 0.70 |
| 3 | A1 relics | `wackysDatabase/Items|Recipes`, `WackyMole.ItemRequiresSkillLevel.yml`, `loot/drops.csv`, `loot/collection-log.csv`, bank cfg | gen-loot, validate, sim method scenario at about 8 h |
| 4 | A2 sets | same wackydb folders + `Effects/SE_OSRS_Set*`, `loot/objects.csv` | share and `RATE_CAP` pass; sim dungeons-per-set in target |
| 5 | C saga | `Quests/osrsheim_quests_story.cfg`, `QuestEvents/`, `QuestProfiles/`, belt item and recipe, WIRSL | validator key check; sim grants key |
| 6 | D journeys | `Gamblers/osrsheim_gamblers.cfg`, `Dialogues/osrsheim_dialogues.cfg`, `Marketplace_SavedNPCs/*.yml`, `reference/npc-layout.csv` (via `gen-npcs.py`), scroll and casket items | validator prefab and HasItem checks; sim journey cost |
| 7 | Player-facing text + docs | see below | `doc-guard.py` and `collection-guard` pass |
| 8 | Run-through + ship | GitHub #156 | every box ticked; PR merged; hand-off to Sven |

**Tooling changes (step 1):**
- `scripts/gen-loot.py`
  - Parse the `skill=` token.
  - Keep one shared `SKILL_TYPES` set taken from the decompile.
  - Emit `ConditionKilledBySkillType`.
  - Reject `skill=` combined with `unique=` or `one-per-player`.
  - Check that `update-superiors.py` never copies a conditional row.
- `scripts/post-build-check.py`: import the shared parser instead of the second whitelist at :168.
- `scripts/sim-run.py`
  - `load_drops()` routes `ConditionKilledBySkillType` rows into a `method` table.
  - Self-check 7 skips `skill=` rows.
  - Add a dedicated-hunt scenario.
  - Grant keys from any QuestEvents `AddPlayerKey`, replacing the `*_seal`-only logic at :1158-1160.
  - Charge journey travel time.
  - Read the pet N_i rows.
- `scripts/validate-configs.py`
  - Derive the clone count from the collection log + exemptions instead of the hard-coded 106 at :122.
  - Accept any key granted by QuestEvents, not just `oath_*`.
  - Every relic-crafted clone has a WIRSL gate.
  - Set pieces have a unique `m_setName`.
  - `SE_SET_Equip` names an existing SE.
  - Every Gambler cost/prize and dialogue `HasItem` prefab exists.
  - `skill=` enum values are valid.
- `scripts/gen-handbook.py`
  - Show the condition in the row tail.
  - New "Chest finds" section for object drops.
- `scripts/gen-collection-log.py` audit: `OSRS_Scroll*` exemption.

**Player-facing text + docs (step 7):**
- Regenerate the handbook and collection log.
- `ServerInfos/osrsheim_guide.cfg`: the relic, dungeon set, pet, saga and journey lines; fix the pet line at :57.
- One fact per line in `research/loot.md` §7 (relics, chests, pets, Drop That condition facts), `research/gating.md` §6/§8 (gates, set syntax) and `research/marketplace.md` §11 (saga, cairns, gamblers).
- STATE: replace the lines in place and prune to stay ≤ 3.5 KB.
- README glossary gets "Relic" only after pruning to fit.

## Verification: official run-through (posted to #156 in its format)
**Stage 1: automated.**
```
python scripts/gen-loot.py; python scripts/gen-objects.py; python scripts/gen-collection-log.py; python scripts/gen-handbook.py; python scripts/gen-npcs.py
python scripts/validate-configs.py --repo
python scripts/post-build-check.py --repo
python scripts/sim-run.py validate; python scripts/sim-run.py run
echo '{}' | python scripts/doc-guard.py
```
Expected: 0 errors, `gen-* --check` clean. The sim reports pets ≈ 1.2 per player-run, method relics about 8 h dedicated, sets inside the dungeon target, and journey cost charged.

**Stage 2: ModTest solo** (`sync-configs.ps1 -Push -Solo`, launch, `devcommands`). One `- [ ] action -> expected` per line:
- Load log: WIRSL `Loaded:` count = old + new gates; no wackydb "missing m_weight" or unknown-prefab warnings.
- A1, each family:
  - Spawn the creature and kill it with the right skill → relic can drop (use `gen-loot.py --wiring` for 100%).
  - Wrong skill → never.
  - Burn kill → never.
  - Craft is blocked below the gate and allowed at it (`raiseskill`).
  - The twist shows in the tooltip.
- A2, each chest: `--wiring` the chest row → relic appears; each piece crafts; the set bonus appears at 3 clone pieces and not with vanilla pieces; an upgrade costs no relic.
- B: handbook shows the new pet rates; `--wiring` a boss → pet drops for each player.
- C: belt uncraftable → finish 6 quests → key (`listkeys`) → craftable → swim stamina visibly halved.
- D: place 2 test cairns via builder → read T3 stone → scroll → cairn reply appears only while holding its scroll → casket → `riddle_elaborate` opens with the casket.
- Collection log: Halla lights every new item.
- Bank accepts relics and caskets.
- Restore plain generators after the wiring tests (`--check` clean).

**Stage 3: two players** (local test server): a relic goes only to the killer; a boss pet roll behaves as expected for both players; each player needs their own saga key; a cairn journey works for both.

**Stage 4: Gielheim**
1. Merge the PR and `sync-configs.ps1 -Push`.
2. Sven deploys to the host.
3. Doug creates the world.
4. The admin places 8 cairns on site (`gen-npcs.py --set`).
5. First-session log read.

The STATE watch list gains: method-hunt hours, dungeons per set, journey length.
