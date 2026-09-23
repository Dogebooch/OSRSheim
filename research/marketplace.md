# OSRSheim research — KG Marketplace

§11 of the reference; hub and section map: [`RESEARCH.md`](../RESEARCH.md).

## 11. KG Marketplace

Docs: https://kg-marketplace.pages.dev/ (config pages under `/configs/`).
Content is plain `.cfg` files under `Marketplace\Configs\<Feature>\`, any
filename, `[profile]` headers, comma-separated fields, hot-reloaded on save.
Bad lines are logged per entry with file and line; the rest still loads.
Only the physical NPC needs the in-game Marketplace Hammer (admin).

`Marketplace\MarketPlace.cfg` changes: `UseLeaderboard = true`,
`AlwaysProgressServerTime = true`, `MarketTaxes = 1`, `CanTeleportWithOre =
false` (the waystones must not carry metal either, §15), `Use Marketplace Locally
= true` (flip to false only once the server exists). Banker interest off.
`DistancedUI` on: `Dialogues = handbook`, `InfoProfiles = gielheim_guide`, every
other list empty, marketplace and mail off (open key unverified).

### Content pack (all `osrsheim_*.cfg`)

**Traders** (`Traders\`) — line = `cost item, amount, result item, amount`.
- `general_store`: buys basics at ~10x sell price (Wood 3c to FishingRod
  350c); sells wood, stone, hides 10-60c, trophies 5-200c, fish 3-50c.
- `gem_trader`: gems 8-80c (25-45% of a kill's value), no `GoldOre`; key forge
  `OSRS_LoopHalfKey, 1, OSRS_ToothHalfKey, 1 = OSRS_CrystalKey, 1`.
- `skillcape_shop`: every cape 5,000c, max cape 25,000c.
- `offerings` (`= true`, Seeress): 150-500c a piece; a summon =
  2.5-2.8x the boss purse. DragonEgg and DvergrKeyFragment wait on a wackydb
  dump. Fader, Kall never.
- `herbwife`: seeds only, no discovery gate, never buys back. CarrotSeeds 10c,
  TurnipSeeds 15c, OnionSeeds 25c per 3. Barley and Flax ARE their own seed so
  they are not sold: bootstrap off `Pickable_<Barley|Flax>_Wild`.
- `supplies` (`= true`, shopkeeper second menu): arrows and bolts 20 a bundle
  60-400c; Wizardry eitr mead bases / soups / plates 20-150c. Vanilla bolts and
  mead bases need a dump. Meads and food are the per-trip drain never bought back.
- `oath_supplies` (`= true` + `HasPlayerKey`): consumables in 50-bundles at ~7%
  off. No gear and nothing WIRSL gates.
- Boss tiers: `offerings`, `supplies`, `oath_supplies`, `herbwife` are cumulative pages
  `<profile>_2..` (each line waits for its biome's boss); the dialogue shows one reply,
  `Condition: GlobalKey, <key>` + `NotGlobalKey` on every later key, `AlwaysVisible: false`.
  Offerings start at `defeated_eikthyr`; Turnip `defeated_bonemass`, Onion `defeated_dragon`.

**Bank** (`Bankers\`, profile `bank`): the bankable prefab list is the cfg;
ores, metals, riddle-stones, riddle rewards and oath capes included.

**Gamblers** (`Gamblers\`): `dice_bag` 100c a roll (~5% house edge);
`flower_poker` 1,000c (~11% edge, up to 3 queued rolls); `crystal_chest` 1
OSRS_CrystalKey a roll, 8 uniform prizes; `riddle_simple` / `_cryptic` /
`_elaborate` / `_master` one riddle-stone a roll (§7). All opened from the
Gambler dialogue.

**Story quests** (`Quests\osrsheim_quests_free.cfg` 22 + `osrsheim_quests_story.cfg` 57; one-time via
cooldown 36500; ids OSRS-shaped, text Valheim lore; profile `lumbridge_guide`).
Types: Collect, Kill, Craft, Talk, Harvest. Per biome: a kill, a collect, a
craft of the tier's sword or shield, a fish quest, a boss kill on the previous
boss key; `Skill_EXP` 20-400 on the skill used. Talk intros to 3 NPCs. `Pet:`
tames Boar, Wolf (1 star), Lox. Coins 25c to 8,600c, 108k total. Gated `=
HiddenAnyCondition`, chains `= HiddenOtherQuestCondition`. Six keel quests (§7).

**Hunt contracts** (`Quests\osrsheim_quests_slayer.cfg`, 43,
`= Autocomplete`, cooldown `60s`, biome boss key on line 8; profile
`slayer_master`). Per-task kill counts and pay live in the cfg: 60c (Black Forest
Skeletons) to 4,500c (Deep North witches), a gem on the harder ones; starred
tasks (`creature, 1, 2`, superiors §12, on the spawner's key) 500-2,500c. Camped tasks (Greydwarf, Skeleton, Draugr,
Charred): >= ~14 min at 321 kills/hr x the target's SpawnArea weight share (Greydwarf 5/7, Draugr 4/7,
Charred_Melee 4/12, Charred_Archer 2/12, Charred_Twitcher 5/6), pay 1.25x the §7 coin/hr target for that time. Skip fee
(`QuestEvents\osrsheim_slayer_skip.cfg`, `OnCancelQuest: RemoveItem, Coins,
N`): a third of the pay.

**Herb contracts** (same file, 5 live, `Harvest`, cooldown `1` = a day): `Pickable_<Carrot|Turnip|Onion>` 40, `Pickable_<Barley|Flax>` 60
(`defeated_dragon`); 200-700c + seeds + `Skill_EXP: Farming`. Harvest counts any
Pickable via `Pickable.RPC_Pick`, so own plots count.

**Prayers** (`Buffers\osrsheim_prayers.cfg`, profile `chapel`): 12 buffs,
groups Wards / Might / Vigour / Wisdom / Wayfaring (same group: second buy blocked while one is active).
No condition field exists, so the cost item is the only gate: bones, never
coins. BoneFragments (Meadows) -> WitheredBone (Swamp) -> CharredBone (Ash),
with trophy rungs between. Rungs, traps and block shape: cfg header,
validator-enforced.

**Hiscores** (`LeaderboardAchievements\osrsheim_hiscores.cfg`, 23):
kill milestones per biome, boss kill counts, a craft, explored 25/50/75%,
first and 100th death. IDs are case-sensitive.

**Info page** (`ServerInfos\osrsheim_guide.cfg`, `gielheim_guide`): the rulebook.

**Collection log** (`loot\collection-log.csv` -> `scripts\gen-collection-log.py`
-> `*\osrsheim_collection_log.cfg` in Quests, QuestProfiles, Dialogues;
`--check` / `--audit`, hook `scripts\collection-guard.py`): one Talk quest
`log_<prefab>` per csv row on Halla the Skald, unlock `HasItem, <prefab>, 1`,
target the same NPC, cooldown 36500, 1c, item kept. Dialogue pages per csv
category list each entry gated by `Condition: QuestFinished, log_<prefab>`
(lit = found). Audit: every wackydb clone, drops.csv item and shard needs a
row. Row counts live in the csv; the generator writes into the profile.

**Dialogues**: one root per NPC; each root has an
`OpenUI, <Type>, <profile>` reply. If a reply opens nothing, use bare
`Command: OpenUI`. No commas inside reply text.

**Biome oaths** (achievement diaries; `Quests\osrsheim_quests_oaths.cfg`, profile +
dialogue `oath_keeper`, NPC Sigrun the Oathkeeper). 8 biomes: 40 quests, 36,380c,
8 capes. Per biome 4 PARALLEL tasks on the previous boss key, then a
`= HiddenOtherQuestCondition` seal Talk whose one condition line ANDs the four
`QuestFinished`. The seal fires `QuestEvents\osrsheim_oaths.cfg`
`OnCompleteQuest: AddPlayerKey, oath_<biome>` — `Player.AddUniqueKey`: per-character,
NOT a global key, so Drop That / WIRSL / bounty gates never see it. Perks gate on
`HasPlayerKey` on a dialogue reply: waystones, `oath_supplies`, `chapel_oath`
(4 entry prayers at -40% bone cost, Resolve of Tyr -50%; trophy-gated rungs stay out).

**Teleporters** (`Teleporters\osrsheim_teleports.cfg`, `oath_network_1..8`, Type
Teleporter + Dialogue `waystone`): no gating and no cost in the file — format, the
one-level `@from:` rule and placement rules are in its header. Gate and fee sit
on the reply, 25c to 500c; a row needs its own key AND no higher key. Coordinates:
`set-waystone.py`. Closing the map unused spends the fee.
**Territories**: template only.
**Idle barks**: `Configs\RandomNpcSpeech.yml`, 5 sets (cosmetic). Set key = the NPC's Profile (DLL: lookup by `KGnpcProfile`).

### NPC placement

| Name Override | Type | Profile | Dialogue | Barks |
|---|---|---|---|---|
| Ulfar the Guide | Quests | `lumbridge_guide` | `lumbridge_guide` | yes |
| Huntmaster Hrafn | Quests | `slayer_master` | `slayer_master` | yes |
| Verdandi the Weaver | Trader | `skillcape_shop` | `wise_old_man` | yes |
| Shopkeeper | Trader | `general_store` | `shopkeeper` | — |
| Gullveig | Trader | `gem_trader` | `gem_trader` | — |
| Herbwife | Trader | `herbwife` | `herbwife` | — |
| Banker (two, far apart) | Banker | `bank` | `banker` | yes |
| Gambler | Gambler | `dice_bag` | `gambler` | yes |
| Ragnar the Bold | Gambler | `flower_poker` | — | — |
| Gothi Eirik | Buffer | `chapel` | `chapel` | — |
| Seeress | Trader | `offerings` | `seeress` | — |
| Gielheim Guide | Info | `gielheim_guide` | `handbook` | — |
| Halla the Skald | Quests | `collection_log` | `collection_log` | — |
| Kaupang | Marketplace | — | — | leaderboard tab lives here |
| Sigrun the Oathkeeper | Quests | `oath_keeper` | `oath_keeper` | — |
| Waystone (town + 1 per sworn biome) | Teleporter | `oath_network_1` | `waystone` | — |

Templates: `Marketplace_SavedNPCs\<Name Override>.yml`; placement: `reference\npc-layout.csv` -> `scripts\gen-npcs.py` (Banker 2 rows, Waystone 9).
File-driven placement: dialogue `Command: SpawnXYZWithData,MarketPlaceNPC,1,1,x,y,z,0,<key>` spawns at int x y z (rotation 0, no duplicate check) and writes `Configs\CustomSpawnData\<key>.yml` (Ints/Floats/Strings/Bools/Longs) onto the ZDO; all NPC fields incl. fashion are ZDO keys (`KGmarketNPC` int type, `KGnpcProfile`, `KGnpcDialogue`, `KGnpcNameOverride`, `KGnpcShowCondition`, `KGmarketPinned`). DistancedUI `Dialogues` opens a dialogue with no NPC. Verified ModTest 2026-09-23 (`world-scan.py npcs`).
Far spawns: a new NPC reaches the server only while its placer is within sync range; spawned from afar or left at once, it waits in the client until the next visit (lost on logout). Place far rows on site (builder Go, then Place) and stay ~20 s.
`find MarketPlaceNPC` (devcommands, server-side) finds 0: not a check.
`KGnpcShowCondition`: dialogue condition syntax, checked per client every 2.5 s; false hides model, name and collider; `debugmode` shows all. Verified (oath key toggles the stone).
Teleporter map: keeps the player's fog; shows only the profile's pins.
NPC UI (10.0.1): the Buffer type tile is labelled "Enchanter".
File name = Hammer piece name. `/mreloadnpcs` reloads.
Client-only (`MarketplaceHammer` is a KG Client module): the placing admin's profile needs them; the host never reads them.

### Config audit (2026-09-21)
Evidence: `reference/config-audit-2026-09-21.json`.
Talk / Move targets are bare NPC names, spaces kept, no quotes: DLL-confirmed `ParseTargets`
strips neither and compares against the raw NPC name override.
BetterUI tooltips true: EpicLoot requires false. Cooldown: bare days, `s` seconds.
Everything needing a live world to confirm: the GitHub issue list.
