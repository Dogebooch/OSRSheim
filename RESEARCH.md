# OSRSheim — Research and Build Reference

## 1. The build

Two players, rented dedicated server, 23 mods on Valheim 1.0.15. Skills grind to
100 at half speed; gear gated by skill level. Every creature pays coins and rolls
Gem/Rare tables; bosses drop uniques and pets, elites drop uniques and crystal-key
halves. EpicLoot: maps and bounties only. KG Marketplace: shops, bank, gamblers,
quests, Slayer, prayers, hiscores, biome oaths.

## 2. Where things live

| Thing | Path |
|---|---|
| Mod manager | Gale, `C:\Program Files\Gale\gale.exe`, profile **OSRSheim** |
| Profile root | `C:\Users\drumm\AppData\Roaming\com.kesomannen.gale\valheim\profiles\OSRSheim` |
| Mod configs | repo `config\` is truth -> `<profile>\BepInEx\config\` |
| Load log | `<profile>\BepInEx\LogOutput.log` (Unity copy: `...LocalLow\IronGate\Valheim\Player.log`) |
| Prefab dumps | `<profile>\BepInEx\Debug\` (on world load) |
| Mod manifest (generated) | `reference\mods.tsv` (`scripts\gen-mods.py`) |
| Verified prefab names | `reference\verified-prefab-names.json` |
| Clone base dumps | `reference\wackydb-base-dumps\` |
| Modded launch without Gale | `scripts\launch-modded.ps1` |
| Waystone coordinates | `scripts\set-waystone.py` (§11) |
| Server launch template | `scripts\server-start-template.bat` |
| Backups | `Desktop\Valheim-backup-2026-09-19`, `Desktop\OSRSheim-profile-backup-2026-09-19` |

## 3. Mod stack

Frozen set. Versions: generated `reference\mods.tsv` (`gen-mods.py`), validator
checked. Sources: TS = Thunderstore, HX = Hexium (valheim.hexium.gg). Gale
reads both.

| Mod | Source | Role | Status |
|---|---|---|---|
| BepInExPack Valheim (denikson) | TS | loader | verified |
| Jötunn | TS | library | verified |
| Smoothbrain skills (Mining, Lumberjacking, Cooking, Farming, Building, Sailing, Foraging, Evasion TS; Blacksmithing, Ranching HX) | TS/HX | skills | verified |
| WackyItemRequiresSkillLevel (WIRSL) | TS | gear gating | verified |
| WackysDatabase | TS | item clones, prefab dumps | verified |
| Drop That | TS | creature + object loot | verified |
| Spawn That | TS | superior spawns | loads; untested |
| CreatureLevelAndLootControl (CLLC) | TS | levels display, item yaml | verified |
| EpicLoot | TS | treasure maps + bounties only | loads; untested |
| KG Marketplace (Marketplace And Server NPCs Revamped) | HX | economy, NPCs, quests | configs parse; untested |
| AzuExtendedPlayerInventory | HX | equipment tab + quick slots | verified |
| XPortal | TS | named portals | verified |
| More World Locations AIO | TS | towns and POIs | verified |
| JsonDotNET / YamlDotNet | TS | dependencies | verified |
| Therzie Wizardry | TS | magic ladder Black Forest to Mistlands | loads; gates set, untested |
| OdinPlus PotionPlus | TS | Herblore (Alchemy skill) | loads; §18 keys set, gated §6 |
| Smoothbrain Exploration | HX | Agility feel | verified |
| JuJuz1 SkillGainModifier | TS | vanilla skill XP 0.5x | verified (§18) |
| BetterUI_ForeverMaintained | TS | XP bar | loads; Hexium flags a missing 1.0 method; kept |
| sighsorry Trolling Fishing | TS | bite chance and bonus drops scale with skill (§18) | untested |
| Marlthon OdinShip | TS | 7 hulls, keel-gated (§6, §7, §18) | untested |
| JereKuusela Server devcommands | TS | admin console (§16) | loads |

Version checks without Gale: `thunderstore.io/api/experimental/package/<owner>/<name>/`
and `valheim.hexium.gg/api/v1/package-listing-chunk/` (gzipped, owner `KG`). Install
through Gale only.

## 4. Skill mapping

| OSRS skill | In this build |
|---|---|
| Attack / Strength | vanilla weapon skills (Swords, Clubs, Axes, Polearms, Spears, Knives, Unarmed) |
| Defence | vanilla Blocking |
| Ranged | vanilla Bows, Crossbows |
| Magic | vanilla ElementalMagic, BloodMagic; Wizardry staves below Mistlands |
| Herblore | PotionPlus Alchemy (SkillManager, gain 1x / loss 5% fixed) + Smoothbrain Foraging |
| Hitpoints | none (food) |
| Mining | Smoothbrain Mining |
| Woodcutting | Smoothbrain Lumberjacking |
| Fishing | vanilla Fishing; bait gates §6, bite chance by skill (Trolling Fishing §18) |
| Cooking | Smoothbrain Cooking |
| Smithing | Smoothbrain Blacksmithing |
| Farming | Smoothbrain Farming |
| Construction | Smoothbrain Building |
| Agility | Smoothbrain Evasion (+ vanilla Run/Jump/Swim) |
| Sailing | Smoothbrain Sailing |
| Hunter | Smoothbrain Ranching |
| Slayer | EpicLoot bounties + KG Slayer tasks |
| Prayer | KG Buffer `chapel`, bones as cost (§11) |
| Runecraft, Thieving, Fletching, Firemaking | no analogue |

## 5. Skill settings (Smoothbrain)

Per-mod cfg `org.bepinex.plugins.<skill>.cfg`:

```
Skill Experience Gain Factor = 0.5
Skill Experience Loss = 0
```

Evasion's keys are `Skill gain factor` / `Skill loss`. Skill caps default
(100). Vanilla world skill-gain modifier untouched. Vanilla skills: 0.5x via
SkillGainModifier `Global = 0.5`, death loss `Modifier = 0` (§18).

## 6. Gear gating (WIRSL)

File: `WackyMole.ItemRequiresSkillLevel.yml`. Top-level `Requirements:` list;
each entry is `PrefabName` + a `Requirements` list of `Skill`, `Level`,
`BlockCraft`, `BlockEquip`. Log line on load: `ItemRequiresSkillLevel Loaded:
303`. A wrong PrefabName fails OPEN with no log line. Tiers:
`EpicLoot\baseconfig\iteminfo.json` `ItemsByBoss`.

**Tier ladder**

| Tier | Level | Examples |
|---|---|---|
| Entry | none | SwordBronze, AtgeirBronze, KnifeCopper, FistBjornClaw, BowFineWood, CrossbowArbalest, Black Forest staves |
| Bronze | 15 | MaceBronze, ShieldBronzeBuckler, bronze armor (craft) |
| Iron | 20-25 | SwordIron, BowHuntsman, iron armor, Root / Troll Leather |
| Silver, wolf | 30 | SwordSilver, wolf armor, Fenring |
| Black metal, padded | 40 | SwordBlackmetal, padded armor |
| Mistlands | 50 | carapace, Mistwalker, staves |
| Ashlands (flametal) | 60 | |
| Deep North | 70 | |

**Skill split**

- Weapons: their weapon skill.
- Armor, capes, circlets, trinkets (15 in 1.0): CRAFT on Blacksmithing at
  tier, equip ungated. Shields: EQUIP on Blocking + CRAFT on Blacksmithing.
- Picks: Mining 10 / 20 / 40. One-hand axes: Lumberjacking 15 / 20 / 40 / 50
  (JotunBane) / 70 (Gold). Battleaxes and Berzerkr stay on Axes.
- Staves: ElementalMagic / BloodMagic at 50 / 60 / 70, craft and equip.
  Wizardry: `StaffBlackforest_TW`, `StaffSurtling_TW` ungated, `StaffSwamp_TW` 20,
  `StaffMountain_TW` 30, `StaffPlains_TW` 40 and `StaffGolem_TW` Blood 40,
  `StaffMistlands_TW` 50. Spellslinger sets and circlets 15 / 20 / 30 / 40 /
  50 on the armor split. Rings ungated.
- Unarmed ladder 30-70.
- Crossbows: Arbalest ungated, Ripper 20, Gold 30.
- Skillcapes: skill 100 (max cape ANDs all 23 skills).
- Hellbroths (broth + charge, craft + use): Alchemy 10 Flames, 15 Eternal
  Life, 30 Frost, 40 Thors Fury. Names `Hellbroth_of_<X>` in the 2026-09-21 load log;
  `_Charge` from the DLL only.
- Clone uniques: DragonAxe Lumberjacking 15, DragonfireShield Blocking 30,
  BandosGodsword Swords 40, AbyssalWhip Swords 50, ScytheOfVitur Polearms 70;
  DraugrVisage ungated (armor). Elite uniques (equip, base item's level): HillGiantClub Clubs 15,
  RuneScimitar Swords 20, GraniteMaul Clubs 25, DragonHalberd Polearms 40,
  CrystalBow Bows 50, AbyssalBludgeon Clubs 60, DragonBattleaxe Axes 50.
- Fishing (bait, craft + equip):
  `FishingBaitForest` 10 Trollfish · `Swamp` 20 Giant herring · `Ocean` 25 Tuna,
  Coral cod · `Cave` 30 Tetra · `Plains` 40 Grouper · `Mistlands`
  50 Pufferfish, Anglerfish · `Ashlands` 60 Magmafish · `DeepNorth` 70 Northern
  salmon. Basic bait takes Perch and Pike. Biome bait = 20 basic bait + 1 trophy
  at the food prep table. The rod auto-uses unequipped bait.
- Hulls (`org.bepinex.plugins.sailing.cfg`, helm only): paddle /
  half / full sail Raft 0/0/0 · Karve 5/10/15 · Longship 15/20/30 · Drakkar
  30/40/50. `Exploration Radius Factor = 2`. XP 0.5/s at the helm while
  moving. Full-sail calc: Karve ~15 min, Longship ~70 min,
  Drakkar ~4 h. OdinShip hulls (keel per §7): canoes, Little Boat 0/0/0 ·
  Merchants, Cargo 15/20/30 · Big Cargo 20/30/40 · War Ship 25/35/45.

**Ungated on purpose:** Shovel, HelmetLox, HelmetCrownofValheim, vanilla
capes, SledgeStagbreaker, BowFineWood, ArrowFlint, FishingRod, FishingBait.

**Unverified:** skill name `Alchemy` (would fail open; the vanilla names are
`Skills.SkillType` members). Which skill each vanilla staff uses
(`StaffOrbofAhri`: wikis disagree); check `m_skillType` in a wackydb dump.

## 7. Loot (Drop That)

### Generator
`gen-loot.py` (two `character_drop` cfgs), `gen-objects.py`
(`drop_that.drop_table.cfg`) and `gen-collection-log.py` (three KG cfgs)
write to the **profile**; copy them back to `config\` after a run.
`gen-handbook.py` writes `Dialogues\osrsheim_handbook.cfg` to the repo:
bestiary biome -> creature -> every drop at its real chance, superior
sub-pages, rarity tints per `TIERS`, `COLOUR = False` removes them.
Never hand-edit a generated cfg; all four `--check` in the validator.

Columns are in each generator's docstring. Edit `classes.csv` to rebalance
(multiplier = osrs / valheim), `creatures.csv` to add a creature, `lists.csv` a
shared table, `drops.csv` a creature drop, `objects.csv` an object drop.

`--literal`, `--wiring` and `--marker` leave the cfgs in a test state; the
validator warns until a plain run restores them.

Enforced (CLAUDE.md has the append-only list): lists 110+/120+ keep their
index when merged; `DropOnePerPlayer` per-player roll on a server is
unverified; object entries capped at 5% per destruction and refused on a
table with no vanilla entries. `drop_that.cfg`: dump flags on,
`AlwaysAutoStack = true`. `dropthat:reload` hot-reloads all loot files
(needs `-console`; admin-only on a server).

### Rates
Valheim chance = OSRS chance x (OSRS kills/hr / Valheim kills/hr). Valheim
kills/hr is spawn supply, not kill speed: `python scripts\spawn-rates.py`
prints spawns/hr ceilings from the Spawn That dumps.

Classes (`loot\classes.csv`). Valheim /hr is a guess (ceiling / 3) until
measured with `--marker`. Gem lists roll at camped, Rare lists at elite,
boss uniques at boss; pets stay a literal 0.02 (1/5000):

| Class | Valheim /hr | OSRS /hr | x | 1/512 becomes |
|---|---|---|---|---|
| camped (Greydwarf, Draugr, Skeleton, Charred) | 100 | 400 | 4 | 0.78 (~1/128, ~1.3 h) |
| roamer (Goblin, Wolf, Seeker, Shaman, Wizardry mages) | 25 | 300 | 12 | 2.34 |
| elite (Troll, Golem, Gjall, Brute, _Elite) | 5 | 80 | 16 | 3.13 |
| boss | 2 | 30 | 15 | 2.93 (~1/34, ~17 h) |

### Files
| File | Contents |
|---|---|
| `drop_that.character_drop.cfg` | generated: commons = coins + Gem tier; elites = coins + Rare tier; bosses = coin chunks + trophy + unique `.102` + pet `.103` + riddle-stone `.105` |
| `drop_that.character_drop_list.shared_tables.cfg` | generated: Gem tiers 1-4, Rare tiers 2-5 (T2 coins/necklace gated `defeated_bonemass`), key halves, riddle-stones; every rate lives in `loot\drops.csv` |
| `drop_that.character_drop.osrsheim_superiors.cfg` | generated by `scripts\update-superiors.py` (ROWS): `.200+` coin chunks, `.210` gem, `.211` material, `.212` extra, `.213` rare on the 8 superiors (level 3 + boss key + not tamed); Troll `.200-.210` Meadows purse 100-200c + Ruby |
| `drop_that.drop_table.cfg` | generated by `scripts\gen-objects.py` from `loot\objects.csv`: skilling pet 1/5000, curio 1/500 on 23 `TreeBase` trees and 10 ore tables, gem 1/256 on ore, `TreasureChest_forestcrypt` Coins `w=30` |

Object tables have no per-entry chance: `Weight` is a share of
`DropMin..DropMax` picks, so rarity exists only against the vanilla entries,
`P = DropChance * mean_N[1-(1-w/(W+w))^N]`. Empty vanilla table = fires at
100%; ten `*_log` tables are empty, so woodcutting uses `TreeBase`. No
`Condition*`, no one-per-player. EpicLoot/Smoothbrain/CLLC postfix
`GetDropList` (memory `valheim-getdroplist-multipliers`). No object hook for
Fishing or Farming.

Coin scale: Greydwarf ~2c/kill, Goblin ~4.5c/kill, Charred ~13c/kill, bosses
200-1200c, bounties 150-4800c. Riddle caskets add under 25% at every tier.

Gem tiers: T1 Meadows/Black Forest · T2 Swamp/Mountain/Ocean · T3
Plains/Mistlands · T4 Ashlands/Deep North. Rare tiers: T2 Swamp elites
(bonemass key) · T3 Plains/Mistlands · T4 Ashlands · T5 Deep North.

### Boss uniques and pets
| Boss (prefab) | Unique `.102` @ 2.93% | Pet `.103` @ 0.02% |
|---|---|---|
| Eikthyr | OSRS_GracefulCape (Windrunner cape) | OSRS_PetEikthyr (Sparkfawn) |
| Elder (gd_king) | OSRS_DragonAxe (Rootcleaver) | OSRS_PetElder (Elder sapling) |
| Bonemass | OSRS_DraugrVisage (Bog visage) | OSRS_PetBonemass (Bog lump) |
| Moder (Dragon) | OSRS_DragonfireShield (Drakeskull shield) | OSRS_PetModer (Spiteful hatchling) |
| Yagluth (GoblinKing) | OSRS_BandosGodsword (Yagluth's warblade) | OSRS_PetYagluth (Sulking ember) |
| Queen (SeekerQueen) | OSRS_AbyssalWhip (Queen's lash) | OSRS_PetQueen (Mist broodling) |
| Fader | OSRS_InfernalCape (Cinder cape) | OSRS_JalNibRek (Ember nibbler) |
| Kall (FrozenKing_p3) | OSRS_ScytheOfVitur (Frost King's scythe) | OSRS_PetFrozenKing (Tiny frost king) |

### Elite uniques (`.102`, elite class x16) and crystal chest
| Dropper | Prefab (display) | Base, twist | OSRS rate |
|---|---|---|---|
| Troll | OSRS_HillGiantClub (Troll's knucklebone) | MaceBronze, speed 0.9, stagger 1.5 | 1/256 |
| Draugr_Elite | OSRS_RuneScimitar (Barrow blade) | SwordIron, speed 1.1 | 1/512 (pile-farmable) |
| StoneGolem | OSRS_GraniteMaul (Golemheart hammer) | SledgeIron, stagger 1.5, force 1.5 | 1/256 |
| GoblinBrute | OSRS_DragonHalberd (Warlord's glaive) | AtgeirBlackmetal, dmg 1.1, speed 0.95 | 1/256 |
| Gjall | OSRS_CrystalBow (Gjall-gut bow) | BowSpineSnap, dmg 1.1 | 1/256 |
| Morgen | OSRS_AbyssalBludgeon (Morgen's cudgel) | MaceEldner, speed 1.1 | 1/256 |
| JotunWarrior | OSRS_DragonBattleaxe (Giantsbane axe) | AxeJotunBane, dmg 1.1, stagger 1.3 | 1/256 |

Sleeping / DualWield / NonSleeping variants carry the same row. Twists are
relative multipliers (no base dumps for these bases). Crystal chest:
`OSRS_LoopHalfKey` (Chain clone) + `OSRS_ToothHalfKey` (Needle clone) forge
at Gullveig into `OSRS_CrystalKey` (Crystal clone); the Gambler's
`crystal_chest` takes one key and pays one of 8 uniform prizes (§11).

### Riddle-stones (casket loop)
| Tier | Source | csv |
|---|---|---|
| T1 | Gem T1-T2 | 1/256 |
| T2 | Gem T3-T4 | 1/512 |
| T3 | Rare T2-T3 | 1/512 |
| T4 | Rare T4-T5 1/1024, every boss 100% `.105` one-per-player | |
Prizes uniform: weight = duplicate slots; every line but master carries the next
tier's stone.

### Hull keels (`.104` @ 12.5%, csv `1/120`; one guaranteed by its §11 quest)
| Boss | Keel (clone base) | Display | Hulls |
|---|---|---|---|
| Eikthyr | OSRS_KeelEikthyr (HardAntler) | Antler-carved keel | RowingCanoe, DoubleRowingCanoe, LittleBoat |
| Elder | OSRS_KeelElder (ElderBark) | Heartwood keel | MercantShip |
| Bonemass | OSRS_KeelBonemass (WitheredBone) | Bone-ribbed keel | CargoShip |
| Moder | OSRS_KeelModer (DragonTear) | Drake-tear keel | BigCargoShip |
| Yagluth | OSRS_KeelYagluth (YagluthDrop) | Fuling war-keel | WarShip |
| Queen | OSRS_KeelQueen (QueenDrop) | Dvergr shipwright's keel | WarShip (with Yagluth) |

### Never touch (vanilla progression drops)
Deer trophies + Hard Antler (Eikthyr) · Ancient Seeds + Swamp Key (Elder) ·
Withered Bones + Wishbone (Bonemass) · Dragon Eggs + Dragon Tear (Moder) ·
Fuling Totems (Yagluth) · Sealbreaker fragments + Giant King's Hair (Queen) ·
Fader's items · Malicious Blood (Kall) · Surtling Cores · every boss trophy.

### Statistics
First drop lands around N kills at 1/N; allow ~3N before calling a rate broken
(380 kills for 95% confidence at 1/128).

## 8. Custom items (WackysDatabase)

Folder: `wackysDatabase\Items\Item_OSRS_*.yml`. Base dumps:
`reference\wackydb-base-dumps\`. `Primary_Attack:` needs a `Secondary_Attack:`
block: wackydb dereferences it unguarded and drops the rest of the item's data.
Every yml needs a top-level `m_weight` or wackydb drops it (validator checks).

- 8 boss uniques (table above). Stat twists: Abyssal Whip = Mistwalker clone,
  frost stripped, slash 64, stamina 14, attack speed 1.2; Bandos Godsword
  attack speed 0.9; Scythe of Vitur 0.95.
- 10 pets = trophy clones (8 boss, + Mining/Woodcutting at 1/5000 per
  action); 2 curios = Amber clones, 1/500, sold to the gem trader 35c.
- 7 elite uniques + 3 crystal key parts (§7).
- 4 riddle-stones (AncientGemstone clones) + 6 rewards (4 capes, 2 helmets): armor 0,
  no `SE_Equip` or modifiers, no WIRSL gate, AzuEPI vanity-wearable.
- 24 skillcapes = CapeLinen clones, display `<Valheim skill> cape`, one per skill in
  the §4 table plus `Allfather's cape` (all 23 at 100); equip-gated at 100, no recipe,
  sold by the skillcape shop.
- 6 jewellery = ring/amulet clones, Trinket, gem recipes, Bsmith 15-50.

Clones register and load from cache before world load and drop off kills. Both server and every client need the yml files.

## 9. CLLC

`org.bepinex.plugins.creaturelevelcontrol.cfg`: `Maximum stars = None`,
`Loot system to be used = Vanilla`, `Lock Configuration = On`, `Use item
configuration yaml = On`. Effects and infusions left On (they only roll on
starred creatures, i.e. the superiors). Two-star creatures exist only through
Spawn That.

`ItemConfig.yml` (server-synced): `Coins` weight 0, stack 9999 (verified in
game); Amber, AmberPearl, Ruby weight 0.1 stack 100; SilverNecklace, Chain
weight 0.1 stack 50.

## 10. EpicLoot (restricted)

`randyknapp.mods.epicloot.cfg`: `Global Drop Rate Modifier = 0`, `Adventure
Mode Enabled = true`. `baseconfig\loottables.json`: every table's `Drops` is
`[[0, 100]]` (141 tables + 157 leveled entries, 0 rollable items).

`baseconfig\adventuredata.json` (coins-only economy, untested in game):
- Treasure maps: payouts 0 (2026-09-21) - a pure sink at every tier, the dug
  chest is the whole reward. Cost 100 (Meadows) to 800 (Deep North); Meadows
  chest ~40c; cost is the knob. Runestone items removed.
- Bounties (rare/hard/big): tokens 0, `RewardCoins` x6 (150 -> 4800); Iron
  lvl 3 @3x HP, Gold @4.5x, adds lvl 2-3 @2x HP.
- Bounty cfg: `Gated Bounty Mode = BossKillUnlocksCurrentBiomeBounties`,
  `Enable Bounty Limit = true`, `Max Bounties Per Player = 1`.
- Gamble tab: all counts 0. Secret Stash: only Andvaranaut (1998c).

Backups `.bak-osrsheim`; redo both edits if an update refreshes `baseconfig`.

## 11. KG Marketplace

Docs: https://kg-marketplace.pages.dev/ (config pages under `/configs/`). Content is
plain `.cfg` under `Marketplace\Configs\<Feature>\`, any filename, `[profile]`
headers, comma-separated fields, hot-reloaded on save. A bad line is logged with its
file and line; the rest of the file still loads.
Only the NPC itself needs the in-game Marketplace Hammer (admin).

`MarketPlace.cfg` changes: `UseLeaderboard = true`,
`AlwaysProgressServerTime = true`, `MarketTaxes = 1`, `CanTeleportWithOre =
false` (the waystones must not carry metal either, §15), `Use Marketplace Locally
= true` (flip to false only once the server exists). Banker interest off.
`DistancedUI` on: `Dialogues = handbook`, `InfoProfiles = gielheim_guide`, every
other list empty, marketplace and mail off (open key unverified).

### Content pack (all `osrsheim_*.cfg`)

**Traders** (`Traders\`) — line = `cost item, amount, result item, amount`.
- `general_store`: buys basics at ~10x sell price; sells wood stone hides 10-60c,
  trophies 5-200c, fish 3-50c.
- `gem_trader`: gems 8-120c (25-45% of a kill's value); key forge
  `OSRS_LoopHalfKey, 1, OSRS_ToothHalfKey, 1 = OSRS_CrystalKey, 1`.
- `skillcape_shop`: any cape 5,000c, max cape 25,000c.
- `offerings` (`= true` discovery gate, Seeress): 150-500c a piece; a summon =
  2.5-2.8x the boss purse. DragonEgg and DvergrKeyFragment wait on a wackydb
  dump. Fader, Kall never.
- `supplies` (`= true`, shopkeeper second menu): arrows and bolts 20 a bundle
  60-400c; Wizardry eitr mead bases / soups / plates 20-150c. Vanilla bolts and
  mead bases need a dump. Meads and food are the per-trip drain never bought back.
- `oath_supplies` (`= true` + `HasPlayerKey`): the same consumables in 50-bundles
  at ~7% off. No gear and nothing WIRSL gates.

**Bank** (`Bankers\`, profile `bank`): 162 bankable prefabs including ores, metals,
riddle-stones, rewards and oath capes.

**Gamblers** (`Gamblers\`): `dice_bag` 100c a roll (~5% house edge);
`flower_poker` 1,000c (~11% edge, up to 3 queued rolls); `crystal_chest` 1
OSRS_CrystalKey a roll, 8 uniform prizes; `riddle_simple` / `_cryptic` /
`_elaborate` / `_master` one riddle-stone a roll (§7). Prize tables are in the
cfg. All opened from the Gambler dialogue, node `gambler_riddles`.

**Story quests** (`Quests\osrsheim_quests_free.cfg` 22 live + `osrsheim_quests_story.cfg`
57 staged in `staging\quest-pass\`; one-time via cooldown 36500; profile
`lumbridge_guide`).
Types: Collect, Kill, Craft, Talk, Harvest. Per biome: a kill, a collect, a craft of
the tier's sword or shield, a fish quest, a boss kill (unlocks on the PREVIOUS boss
key). `Skill_EXP` 20-400. Talk intros to 3 NPCs. `Pet:` rewards: Boar, Wolf
(1 star), Lox. Coins 25c (Meadows) to 8,000c (Deep North),
107k total. `= HiddenAnyCondition` hides until open, `= HiddenOtherQuestCondition`
until the named quest is done. Six hull keel quests (§7), one keel each.

**Hunt contracts** (`Quests\osrsheim_quests_slayer.cfg`, 43 staged, `= Autocomplete`,
cooldown `60s`, biome boss key; profile `slayer_master`). Kill counts and pay live in
the cfg. Pay by biome: Meadows 80-150, Black Forest 200-300, Swamp 250-500, Mountain
500-900, Plains 700-1000, Mistlands 1200-2000, Ashlands 2000-4000, Deep North
3000-4500; each biome's hardest contract also pays a gem. Starred variants
(`creature, 1, 2`, §12) pay 500-2500.
Skip fee (`QuestEvents\osrsheim_slayer_skip.cfg`, `OnCancelQuest: RemoveItem, Coins,
N`): a third of the pay.

**Prayers** (`Buffers\osrsheim_prayers.cfg`, profile `chapel`): 12 buffs,
groups Wards / Might / Vigour / Wisdom / Wayfaring (same group = exclusive).
No condition field exists, so the cost item is the only gate: bones, never
coins. BoneFragments (Meadows) -> WitheredBone (Swamp) -> CharredBone (Ash),
with trophy rungs between. Rungs, traps and block shape: cfg header,
validator-enforced.

**Hiscores** (`LeaderboardAchievements\osrsheim_hiscores.cfg`, 23): kill milestones
per biome, boss kills, a craft, explored 25/50/75%, first and 100th death.
IDs are case-sensitive.

**Info page** (`ServerInfos\osrsheim_guide.cfg`, `gielheim_guide`): the rulebook.
**Collection log** (`loot\collection-log.csv` -> `gen-collection-log.py` ->
`*\osrsheim_collection_log.cfg` in Quests, QuestProfiles, Dialogues; `--check` /
`--audit`, hook `collection-guard.py`): one Talk quest
`log_<prefab>` per csv row on Halla the Skald, unlock `HasItem, <prefab>, 1`,
target the same NPC, cooldown 36500, 1c, item kept. Dialogue pages per csv
category list each entry gated by `Condition: QuestFinished, log_<prefab>`
(lit = found). Audit: every wackydb clone, drops.csv item and shard needs a
row. Row counts live in the csv; the generator writes into the profile.

**Collection log** (`loot\collection-log.csv` -> `scripts\gen-collection-log.py`
-> `*\osrsheim_collection_log.cfg` in Quests, QuestProfiles, Dialogues;
`--check` / `--audit`, hook `scripts\collection-guard.py`): 137 Talk quests
`log_<prefab>` on Halla the Skald, unlock `HasItem, <prefab>, 1`, target the
same NPC, cooldown 36500, 1c, item kept. Dialogue pages per category list
each entry gated by `Condition: QuestFinished, log_<prefab>` (lit = found).
Row counts per category live in the csv. Audit: every wackydb clone, drops.csv item
and shard needs a row.

**Biome oaths** (achievement diaries; `Quests\osrsheim_quests_oaths.cfg`, profile +
dialogue `oath_keeper`, NPC Sigrun the Oathkeeper). All 8 biomes: 40 quests, 36,380c,
8 capes. Per biome 4 PARALLEL tasks on the previous boss key, then a
`= HiddenOtherQuestCondition` seal Talk quest whose one condition line ANDs the four
`QuestFinished`. The seal fires `QuestEvents\osrsheim_oaths.cfg`
`OnCompleteQuest: AddPlayerKey, oath_<biome>` — `Player.AddUniqueKey`, per-character,
NOT a global key, so Drop That / WIRSL / bounty gates never see it. Perks gate on
`HasPlayerKey` on a dialogue reply: waystones, `oath_supplies`, `chapel_oath`
(4 entry prayers at -40% bone cost; trophy-gated rungs stay out).

**Teleporters** (`Teleporters\osrsheim_teleports.cfg`, `oath_network_1..8`, Type
Teleporter + Dialogue `waystone`): NO gating and no cost in the file — format, the
one-level `@from:` rule and the placement rules are in its header. Gate and fee sit
on the reply, 25c to 500c; a row needs its own key AND no higher key, so exactly one
shows. Coordinates: `set-waystone.py`. Closing the map unused spends the fee.
**Territories**: template only; fill coordinates from the in-game `pos` command.

**Idle barks**: `RandomNpcSpeech.yml`, 5 sets.

### NPC placement

| Name Override | Type | Profile | Dialogue | Speech set |
|---|---|---|---|---|
| Ulfar the Guide | Quests | `lumbridge_guide` | `lumbridge_guide` | `guide_idle` |
| Huntmaster Hrafn | Quests | `slayer_master` | `slayer_master` | `slayer_idle` |
| Verdandi the Weaver | Trader | `skillcape_shop` | `wise_old_man` | `wise_old_man_idle` |
| Shopkeeper | Trader | `general_store` | `shopkeeper` | — |
| Gullveig | Trader | `gem_trader` | `gem_trader` | — |
| Banker (two, far apart) | Banker | `bank` | `banker` | `banker_idle` |
| Gambler | Gambler | `dice_bag` | `gambler` | `gambler_idle` |
| Ragnar the Bold | Gambler | `flower_poker` | — | — |
| Gothi Eirik | Buffer | `chapel` | `chapel` | — |
| Seeress | Trader | `offerings` | `seeress` | — |
| Gielheim Guide | Info | `gielheim_guide` | `handbook` | — |
| Halla the Skald | Quests | `collection_log` | `collection_log` | — |
| Kaupang | Marketplace | — | — | leaderboard tab lives here |
| Sigrun the Oathkeeper | Quests | `oath_keeper` | `oath_keeper` | — |
| Waystone (town + 1 per sworn biome) | Teleporter | `oath_network_1` | `waystone` | — |

### Config audit (2026-09-21)
Evidence: `reference/config-audit-2026-09-21.json`; configs unchanged.
**Unfixed:** 138 Talk targets retain quotes; remove them and keep the spaces, fix
the collection generator. DLL-confirmed: `ParseTargets` strips neither spaces nor
quotes for Talk / Move and compares against the raw NPC name override.
BetterUI tooltips true: EpicLoot requires false. Cooldown: bare days, `s` seconds.
Runtime unverified: icons/VFX, rich text, discovery gates, skip fee, fish quality,
Pet/Harvest, custom-skill XP, multi-cost trades, gambling.

## 12. Superiors and wanderers (Spawn That)

File: `spawn_that.world_spawners_advanced.cfg`. Docs:
github.com/ASharpPen/Valheim.SpawnThat/tree/development/src/SpawnThat.Docs.
IDs 0-102 are occupied (44+ modded); ours use 500+. No reload command: exit to
the menu and re-enter. `spawnthat wheredoesitspawn <id>` and `arearollheatmap
<id>` write PNGs to `BepInEx\Debug\`.

| ID | Spawn | Biome / key |
|---|---|---|
| 500-507 | Superior Greydwarf, Skeleton, Draugr, Wolf, Goblin, Seeker, Charred_Melee, JotunWarrior: `LevelMin/Max = 3`, `UseDefaultLevels = true`, `SetExtraEffect` (e.g. Regenerating), 8% per 900 s check, cap 1 | each biome, gated by the previous boss key |
| 510 | Wandering Meadows night troll, 20% per 1200 s (~one per 5 h of nights), >300 m from center, no HuntPlayer | Meadows, `defeated_eikthyr` |
| 511 | Fuling scouts, 2-3, night only, 20% per 1200 s, >500 m from center | Black Forest, `defeated_bonemass` |

Biome enum: Meadows, BlackForest, Swamp, Mountain, Plains, Mistlands,
AshLands, DeepNorth. Their loot is the superiors file (§7), which fails closed
if CLLC clamps the level. Fallback if superiors spawn at zero stars: CLLC
`Maximum stars = Two` with all star chances 0.

`SpawnDistance` = no other spawn of the same prefab within range. 0 on 500-507
on purpose: they share the common prefab, so any value suppresses them. 200 on
510, 150 on 511. Anchors add `blackforge`, and 510 `piece_workbench` (the only
station an Eikthyr-era base has). The cfg is generated by
`update-superiors.py` from `ANCHOR_LIST` — never hand-edit it.

## 13. World, inventory, travel

- **More World Locations AIO**: `Enable Trainers = Off`, `Use Custom Trader
  Configs = On`, `Use Custom Location YAML = On`. First launch writes
  `..._TraderItems.yml` (Skill Books and Blacksmith Stones removed, trainer lists
  emptied) and `..._LocationConfigs.yml` (188 location types). Locations bake at
  world-gen: tune before Gielheim exists.

- **AzuEPI slots**: reserved `m_itemType`; `BlockCraft` not `BlockEquip`.

## 15. Server setup

- Flags (valheimgame.com/support/a-guide-to-dedicated-servers/): `-preset`,
  `-modifier combat|deathpenalty|resources|raids|portals <value>`, `-setkey`.
  Template: `scripts\server-start-template.bat`. Chosen: `-modifier
  deathpenalty casual`; `portals` left at default (vanilla, no metal) — the earned
  KG waystone network is the travel reward, and `CanTeleportWithOre = false`
  keeps metal off it too (§11).
- Deploy payload = the Gale profile root: `winhttp.dll`,
  `doorstop_config.ini` (relative target, works unchanged), `doorstop_libs\`,
  `BepInEx\`. Linux hosts use `start_server_bepinex.sh`.
- Same versions on host and both clients: `python scripts\gen-mods.py --verify
  <host BepInEx\plugins | its LogOutput.log>`. ServerSync'd: all Smoothbrain
  skills, CLLC, WIRSL (`Lock Configuration = On`), EpicLoot, AzuEPI,
  WackysDatabase, MWL, Trolling Fishing. Drop That clients pull the server's loaded
  configs.
- `adminlist.txt` needs Doug's SteamID64 (76561198855908341) for
  `devcommands` and `dropthat:reload`.
- Flip KG `Use Marketplace Locally = false` at standup, then check Trader,
  Banker, Quests, Teleporter one by one.
- Friend joins via Gale profile export (Hexium mods require Gale, not
  r2modman). The export carries the clone ymls.
- Backups: Gale profile + host world save; stop the server via its own
  shutdown (§16).

## 16. Testing knowledge

**Console** (`-console`, F5): `devcommands`, `god`, `debugmode`, `spawn
<Prefab> <count> <level>` (3 = two stars), `killall`, `removedrops`,
`raiseskill <Skill> <n>`, `setkey` / `resetkeys`, `tod 0.9` / `tod -1`, `pos`,
`dropthat:reload`, `location Vendor_BlackForest` (disables saving).

**Wiring session** (proves entries fire): `gen-loot.py --wiring`, validate, launch,
`devcommands`, `god`, `setkey defeated_bonemass`; spawn Greydwarf 3 (gems),
Draugr_Elite 2 (Rare T2, key halves, unique), Eikthyr 1 (purse, unique, pet),
`setkey defeated_frozenking_p3` + JotunWarrior 1 3 (superior). Then `gen-loot.py`,
`dropthat:reload`, `removedrops`, `resetkeys`, Logout. The console takes synthetic
typing only right after F5.

**Post-build**: `scripts\post-build-check.py` - EOL against HEAD, clone ymls, csv
shape, gambler lines, repo/profile parity, validator.

**Log reading**: `LogOutput.log` is the source of truth. Find the first
NullReferenceException and read down to the first frame that is not
UnityEngine / ObjectDB / ZNetScene. `MissingMethodException` on a Harmony
`DMD<...>` frame means a pre-1.0 plugin: scan plugin DLL MemberRefs for the
old signature (Valheim 1.0 `Character.Message` takes five args, pre-1.0
four). Item pickups log `Queue unlock msg` on first-ever pickup only.
`Removing orphan save file` is a red flag, not noise.

**Save safety**: 1.0 deletes a world whose main files are newer than its
`.ok.stmp`. Logout, wait for the save, then Quit.

**Vanilla names in no dump**: `grep -a` the `SoftRef` bundles under
`valheim_Data\StreamingAssets`.

## 17. Bugs found and fixed (so they are not re-found)

| Symptom | Cause | Fix |
|---|---|---|
| Shared list overwrote Greydwarf eye/stone/wood | list entries at index 0-2 | lists at 110+/120+ |
| `DraugrFang` gate never fired | wrong prefab | `BowDraugrFang` |
| Magic gear still dropped with Global Drop Rate 0 | elite/boss tables bypass it | zero `loottables.json` |
| Boss paid 1 coin | `DropOnePerPlayer` forces amount 1 | removed from purses |
| 150-coin purse paid 100 | 100-item cap per entry | split into chunks |
| `raiseskill` silently did nothing | Blacksmithing 1.3.5 4-arg `Character.Message` | 1.3.6 from Hexium |
| NRE spam from Ranching at world load | Ranching 1.1.8 | 1.1.9 |
| CLLC AmbiguousMatch | Valheim1CompatBridges | removed |
| Test world vanished | orphan-save discard after a hard kill | never kill with a world loaded |
| Troll trophy name | `TrophyTroll` does not exist | `TrophyFrostTroll` |
| Copper rock name | `rock4_copper` gone in 1.0.15 | `MineRock_Copper` |
| 7 elite uniques never loaded | Item yml without `m_weight` | dumped base weight; validator errors |

## 18. Wave B and backlog

### Wave B settings

| Mod | Cfg file | Settings | Notes |
|---|---|---|---|
| OdinPlus PotionPlus | `com.odinplus.potionsplus.cfg` | `Lock Configuration = On`; wand, dragon staff, both hats `Crafting Station Level = 99`. Hellbroths stay (§6) | Skill `Alchemy` (= Herblore): 1 XP per craft at `opalchemy`; gain 1x / death loss 5% hard-coded. Stations `opalchemy`, `opcauldron`; base `Potion_Meadbase`. |
| Smoothbrain Exploration | `org.bepinex.plugins.exploration.cfg` | `Skill Experience Gain Factor = 0.5`, `Skill Experience Loss = 0`, `Treasure Multiplication Chance = 0` | Treasure doubling condition is inverted in source. Speed +15 / radius +250 at 100; cartography write 20 / read 40. All keys ServerSync. |
| JuJuz1 SkillGainModifier | `jujuz1.mods.skillgainmodifier.cfg` | `Logging Enabled = false`, `Duration = 50` (corpse-run seconds), `[Skill Gain] Global = 0.5`, `Fishing = 3`, `[Skill reduction] Modifier = 0` | Vanilla skills only; logging off or it errors per modded XP tick. No sync: same cfg on both clients. Per-skill keys under `[Skill Gain]` (0 = use Global). |
| Marlthon OdinShip | `marlthon.OdinShip.cfg` | `OSRS_Keel<Boss>:1:False` appended to the 7 hull `Crafting Costs`, War Ship takes Yagluth + Queen; everything else default, BepInEx writes the full file on first launch | Sections by display name, apostrophes stripped (`[Merchants boat]`); costs `Prefab:amount:recover`. Ship mats from the Carpenters Table. |
| sighsorry Trolling Fishing | `sighsorry.TrollingFishing.cfg` | `Lock Configuration = On`, `Fishing Bite Chance Bonus Factor = 0.3`, `Fishing Extra Drop Chance Bonus Factor = 1`, `Fishing Rod Bag = Off`, `Fishing Rod Multi Line = Off` | ServerSync. Writes `TrollingFishing.yml` (bait each fish nibbles + chance) on first launch. |

### Planned

- **Optional heavy content**: Therzie Warfare 1.9.2 + Armory 1.4.0, Monstrum.
- **Ironman** is self-imposed (no marketplace, no trading; banker allowed).
- **Knobs to tune by feel**: skillcape price, gem prices, trophy prices,
  Slayer rewards, superior rarity (8% / 900 s), treasure map payout (1.5x),
  gambler edge, market tax, waystone fee (25 / 50 / 100c), Goblin double coins,
  clone attack speeds, Fishing
  XP factor, fish sale prices, bite chance at 100,
  Wizardry Swamp-tier gear (reported strong; gate 20).

## 19. Dead ends

Almanac 3.7.94 (crashes on 1.0) · Boat mods: BoatAdditions, CustomShips (stale), Balrond shipyard (no cfg),
ValheimRAFT (freeform) · RtDItems defenders (cosmetic) ·
WackyEpicMMOSystem (single-level model) · EpicLoot affix drops on creature
tables (random rolls break fixed-item identity, the collection log, WIRSL tiers) · EpicLoot as the loot pillar · altar
or resummon mods (bosses already resummon freely) · valheim.fandom.com (402;
use valheim.weirdgloop.org).
Fishing: Hooked, PeasFishing (minigames) · Spearfishing (skips bait gates) ·
TheFisher · BetterFishing · FishingBonus · FishChum · Reely.

Magic mods rejected: MagicRevamp, MagicPlugin, Wisdom, SecondaryAttacks,
Jewelcrafting; dead on 1.0: ChebsNecromancy, RtDMagic, MagicalMounts,
MagicOverhaul, Skyheim.

## 20. Sources

- KG Marketplace: https://kg-marketplace.pages.dev/
- Spawn That: https://github.com/ASharpPen/Valheim.SpawnThat/tree/development/src/SpawnThat.Docs
- Drop That: https://github.com/ASharpPen/Valheim.DropThat/wiki
- Dedicated server flags: https://www.valheimgame.com/support/a-guide-to-dedicated-servers/
- Gale: https://github.com/Kesomannen/gale · Hexium: https://valheim.hexium.gg

## 21. Wizardry (Therzie 1.2.0)

Cfg `Therzie.Wizardry.cfg`, ServerSync, `Lock Configuration = On`. Author
says delete the cfg on every update; re-apply the table below after
regenerating. No damage or eitr keys; balance = recipes.

| Edit | Value |
|---|---|
| All 7 pieces `Custom Build Category` | `Wizardry` (was `Warfare`) |
| 10 potions `Custom Crafting Station` | `opalchemy` (was `PotionCauldron_TW`) so they give Alchemy XP |
| Potion Cauldron `Tools` | empty (was `Hammer`) so the piece leaves the build menu |

Content: staves per §6; spellslinger sets, circlets and rings per
`reference\verified-prefab-names.json` (Biome = BlackForest / Swamp /
Mountain / Plains / Mistlands, cape `Blackforest`); mages `GreydwarfMage_TW`
`SkeletonMage_TW` `FenringMage_TW` `GoblinMage_TW` `CorruptedDvergerMage_TW`
drop `Shard<Elder|Bonemass|Moder|Yagluth|Queen>_TW`. README misspells the
Mountain set (`_Mountains_`) and the stamina circlets (`_EitrRegen_`); the
json names are from the DLL. All five mages are `Spawn = Default`, in the 2026-09-21 dump, spawn rates
unreviewed. Mage purses + gem lists in `loot\*.csv` (roamer class).

### Build pieces

Piece prefabs are `piece_*`; recipes point at the bare station names.

All built at the Wizard Table bar the table itself (Workbench). Costs in the
cfg; the shard is the gate:

| Piece | Prefab | Shard gate |
|---|---|---|
| Wizard Table | `piece_wizardtable_TW` | none |
| Arcane Anvil | `piece_arcaneanvil_TW` | Elder 2 |
| Weaving Loom | `piece_weavingloom_TW` | none |
| Ancient Spell Book | `piece_wizardtable_ext2_TW` | Bonemass 2 |
| Spell Cabinet | `piece_wizardtable_ext3_TW` | Moder 2 |
| Ritual Circle | `piece_wizardtable_ext4_TW` | Yagluth 4 |
| Potion Cauldron | `piece_potioncauldron_TW` | Bonemass 2 (off) |

Empty `Tools` is the disable lever (`None` = no station). Whether `ext2..4`
also raise ArcaneAnvil_TW is unverified: hover a level-4 anvil recipe.

### Craft / drop / buy split

| Source | Items |
|---|---|
| Craft, WIRSL-gated | staves, spellslinger sets, circlets, rings, cores, staff bases, yarns, fabric bundles, biome scrolls |
| Drop first, craft after | `Shard*_TW` from the five mages, then ArcaneAnvil L1 from metal + a boss trophy (Elder: Bronze 5, AncientSeed 2, TrophyGreydwarfShaman 1). The anvil itself costs ShardElder_TW 2, so the first shards must drop |
| Buy for coins (`supplies`) | eitr mead bases, soups, plates; buff scrolls Jump 250c, Speed 300c, Slowfall 350c, Damage 500c; `MushroomWizardbutter_TW` 25c, `MushroomDevilstongue_TW` 40c (world-picked, no recipe) |
| Never sold | shards, staves, spellslinger pieces, circlets, rings, biome scrolls — coins must not skip a WIRSL gate or the mage hunt |

Buff scrolls `ArcaneScroll_<DamageBuff|JumpBuff|SlowfallBuff|SpeedBuff>_TW`
(Destruction, Frog, Feather light, Gust) are terminal consumables; biome
scrolls `ArcaneScroll_<Biome>_TW` (Evergrowth, Underworld, Cleansing,
Hellfire, Storm) are the upgrade material and are never sold.
