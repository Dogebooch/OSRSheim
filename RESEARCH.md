# OSRSheim — Research and Build Reference

## 1. The build

Two players, rented dedicated server, 23 mods on Valheim 1.0.15. Skills grind
to 100 at half speed; gear gated by skill level, tier by tier. Every creature
pays coins and rolls Gem/Rare tables; bosses drop signature uniques and pets at
fixed rates; elites drop uniques and key halves for a crystal chest. EpicLoot:
treasure maps and bounties only. KG Marketplace: shops, bank, gamblers, quests,
Slayer tasks, prayers, hiscores.

## 2. Where things live

| Thing | Path |
|---|---|
| Mod manager | Gale, `C:\Program Files\Gale\gale.exe`, profile **OSRSheim** |
| Profile root | `C:\Users\drumm\AppData\Roaming\com.kesomannen.gale\valheim\profiles\OSRSheim` |
| Mod configs | repo `config\` is truth -> `<profile>\BepInEx\config\` |
| Load log | `<profile>\BepInEx\LogOutput.log` (Unity copy: `%USERPROFILE%\AppData\LocalLow\IronGate\Valheim\Player.log`) |
| Prefab dumps | `<profile>\BepInEx\Debug\` (written on world load) |
| Game | `C:\Program Files (x86)\Steam\steamapps\common\Valheim` (app 892970) |
| Local saves | `%USERPROFILE%\AppData\LocalLow\IronGate\Valheim` (test worlds only) |
| Verified prefab names | `reference\verified-prefab-names.json` |
| Clone base dumps | `reference\wackydb-base-dumps\` |
| Modded launch without Gale | `scripts\launch-modded.ps1` |
| Server launch template | `scripts\server-start-template.bat` |
| Backups | `Desktop\Valheim-backup-2026-09-19`, `Desktop\OSRSheim-profile-backup-2026-09-19`, `archive\config-snapshot-2026-09-20.zip` |

## 3. Mod stack

Versions are the pinned, loading-clean set as of 2026-09-20. Sources: TS =
Thunderstore, HX = Hexium (valheim.hexium.gg). Gale reads both.

| Mod | Version | Source | Role | Status |
|---|---|---|---|---|
| BepInExPack Valheim (denikson) | 5.4.2350 | TS | loader | verified |
| Jötunn | 2.30.2 | TS | library | verified |
| Smoothbrain Mining | 1.1.7 | TS | skill | verified |
| Smoothbrain Lumberjacking | 1.0.7 | TS | skill | verified |
| Smoothbrain Cooking | 1.2.3 | TS | skill | verified |
| Smoothbrain Farming | 2.2.3 | TS | skill | verified |
| Smoothbrain Blacksmithing | 1.3.6 | HX | skill | verified |
| Smoothbrain Building | 1.2.7 | TS | skill | verified |
| Smoothbrain Sailing | 1.1.9 | TS | skill | verified |
| Smoothbrain Ranching | 1.1.9 | HX | skill | verified |
| Smoothbrain Foraging | 1.0.11 | TS | skill | verified |
| Smoothbrain Evasion | 1.0.5 | TS | skill | verified |
| WackyItemRequiresSkillLevel (WIRSL) | 1.4.7 | TS | gear gating | verified |
| WackysDatabase | 2.5.34 | TS | item clones, prefab dumps | verified |
| Drop That | 3.1.5 | TS | creature + object loot | verified |
| Spawn That | 1.2.19 | TS | superior spawns | loads; spawns untested |
| CreatureLevelAndLootControl (CLLC) | 5.0.4 | TS | levels display, item yaml | verified |
| EpicLoot | 0.14.11 | TS | treasure maps + bounties only | loads; economy untested |
| KG Marketplace (Marketplace And Server NPCs Revamped) | 10.0.1-beta.1 | HX | economy, NPCs, quests | configs parse; NPCs untested |
| AzuExtendedPlayerInventory | 2.5.1 | HX | equipment tab + quick slots | verified |
| XPortal | 1.2.25 | TS | named portals | verified |
| More World Locations AIO | 5.1.1 | TS | towns and POIs | verified |
| JsonDotNET / YamlDotNet | 13.0.4 / 16.3.1 | TS | dependencies | verified |
| Therzie Wizardry | 1.2.0 | TS | magic ladder Black Forest to Mistlands | loads; gates + cfg set, untested in world |
| OdinPlus PotionPlus | 4.3.4 | TS | Herblore (Alchemy skill) | loads; §18 keys set, hellbroths gated (§6) |
| Smoothbrain Exploration | 1.0.5 | HX | Agility feel | loads; cfg untouched |
| JuJuz1 SkillGainModifier | 0.1.1 | TS | vanilla skill XP 0.5x | loads; cfg untouched, unverified on 1.0 |
| BetterUI_ForeverMaintained | 2.5.12 | TS | XP bar | loads; Hexium flags `Smelter.UpdateHoverTexts` missing on 1.0; kept |
| sighsorry Trolling Fishing | 1.1.3 | TS | Fishing bite chance and bonus drops scale with skill (§18) | installed 2026-09-21, untested |
| Marlthon OdinShip | 0.8.1 | TS | 7 hulls, keel-gated (§6, §7, §18) | installed 2026-09-21, untested |

Update checks without Gale: `https://thunderstore.io/api/experimental/package/<owner>/<name>/`,
`https://valheim.hexium.gg/api/v1/package-listing-chunk/` (gzipped, owner `KG`).
Install: `ror2mm://v1/install/thunderstore.io/<owner>/<name>/<version>/`.

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
| Prayer, Runecraft, Thieving, Fletching, Firemaking | no analogue |

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
  Life, 30 Frost, 40 Thors Fury. Names `Hellbroth_of_<X>[_Charge]` from the
  DLL; not yet in a dump.
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
`python scripts\gen-loot.py` writes `drop_that.character_drop.cfg` and
`drop_that.character_drop_list.shared_tables.cfg` from `loot\*.csv`. The
validator fails when cfgs and tables differ. Never hand-edit those two cfgs.

| Table | Columns | Edit it to |
|---|---|---|
| `loot\classes.csv` | class, valheim_kills_hr, osrs_kills_hr | rebalance: multiplier = osrs / valheim |
| `loot\creatures.csv` | biome, creature, class, list | add a creature; its one `UseDropList` |
| `loot\lists.csv` | list, class, first_id (Gem 110, Rare 120) | add a shared table |
| `loot\drops.csv` | owner, item, min, max, chance, flags, id | add or change a drop |

`chance`: `30` = flat percent (purses, pets, trophies); `1/256` = OSRS rate x
the owner's class multiplier (gem, rare and unique items). `flags`:
`one-per-player`, `key=defeated_bonemass`. `id` blank = next free; 102 / 103
pin uniques / pets. Coins above 100 split into <=100 chunks at `.106+`
(creatures) / `.130+` (lists). Flags: `--diff` preview, `--check`, `--literal`
(multipliers 1), `--wiring` (every chance 100), `--marker <Creature> <Item>`
(100% x1 kill counter); the validator warns until a plain run restores them.

Enforced: IDs >= 100 (vanilla drops at 0-2 never cleared); lists 110+/120+
keep their index when merged; `ScaleByLevel = false`; <= 100 items per entry;
`DropOnePerPlayer` only on amount-1 items (per-player roll on a server
unverified). `drop_that.cfg`: dump flags on,
`AlwaysAutoStack = true`. `dropthat:reload` hot-reloads all loot files
(needs `-console`; admin-only on a server).

### Rates
Valheim chance = OSRS chance x (OSRS kills/hr / Valheim kills/hr). Valheim
kills/hr is spawn supply, not kill speed: `python scripts\spawn-rates.py`
prints spawns/hr ceilings from the Spawn That dumps (camps 250-720, roams
2-242 at night, Troll / Gjall / Brute < 1, camps and villages one-shot).

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
| `drop_that.character_drop.cfg` | generated: commons = coins + Gem tier; elites = coins + Rare tier; bosses = flat coins in <=100 chunks + trophy + unique `.102` + pet `.103`; 7 elites = unique `.102` |
| `drop_that.character_drop_list.shared_tables.cfg` | generated: Gem tiers 1-4 (T1 Ruby 1/256, Amber 1/128, AmberPearl 1/512; richer per tier), Rare tiers 2-5 (flat 2-3% coins, SilverNecklace, Chain, Ruby, GoldOre at T5), T2 coins/necklace gated `defeated_bonemass`; key halves Gem T2-4 1/1024, Rare T2-5 1/256 |
| `drop_that.character_drop.osrsheim_superiors.cfg` | generated by `scripts\update-superiors.py` (ROWS): `.200+` coin chunks, `.210` gem, `.211` material, `.212` extra, `.213` rare on the 8 superiors (level 3 + boss key + not tamed); Troll `.200-.210` Meadows purse 100-200c + Ruby |
| `drop_that.drop_table.cfg` | weighted object drops: Feathers on 12 tree logs (bird nest), gems on ore deposits (`MineRock_Copper` etc.), `TreasureChest_forestcrypt` 2-4 picks |

Coin scale: Greydwarf ~2c/kill, Goblin ~4.5c/kill (vanilla 25% x 5-10 plus
ours 30% x 5-15), bosses 200-1200c, bounties 150-4800c.

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
First drop lands around N kills for a 1/N rate; allow ~3N before calling a
rate broken (~380 kills for 95% confidence on 1/128).

## 8. Custom items (WackysDatabase)

Folder: `wackysDatabase\Items\Item_OSRS_*.yml`. wackydb only reads files named
`Item_*.yml`. Never run `wackydb_save_item` onto an authored file (it resets
`Custom_AttackSpeed`). Base dumps: `reference\wackydb-base-dumps\`.

- 8 boss uniques (table above). Stat twists: Abyssal Whip = Mistwalker clone,
  frost stripped, slash 64, stamina 14, attack speed 1.2; Bandos Godsword
  attack speed 0.9; Scythe of Vitur 0.95.
- 8 pets = trophy clones (vanity items).
- 7 elite uniques + 3 crystal key parts (§7).
- 24 skillcapes (display `<Valheim skill> cape`, max = `Allfather's cape`) = CapeLinen clones, equip-gated at skill 100, no recipe, sold
  by the skillcape shop. Cape to skill: Mining, Woodcutting (Lumberjacking),
  Cooking, Farming, Smithing (Blacksmithing), Construction (Building), Sailing,
  Hunter (Ranching), Herblore (Foraging), Agility (Evasion), Fishing, Defence
  (Blocking), Ranged (Bows), Crossbow, Magic (ElementalMagic), BloodMagic,
  Strength (Unarmed), Swords, Knives, Clubs, Polearms, Spears, Axes, Max.

Clones register and load from cache before world load and drop off kills
(verified 2026-09-20). Both server and every client need the yml files.

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
  chest ~40c. Cost is the knob if high tiers feel dead. Runestone items removed.
- Bounties (rare/hard/big): tokens 0, `RewardCoins` x6 (150 -> 4800); Iron
  lvl 3 @3x HP, Gold @4.5x, adds lvl 2-3 @2x HP.
- Bounty cfg: `Gated Bounty Mode = BossKillUnlocksCurrentBiomeBounties`,
  `Enable Bounty Limit = true`, `Max Bounties Per Player = 1`.
- Gamble tab: all counts 0. Secret Stash: only Andvaranaut (1998c).

Backups `.bak-osrsheim`; redo both edits if an update refreshes `baseconfig`.

## 11. KG Marketplace

Docs: https://kg-marketplace.pages.dev/ (config pages under `/configs/`).
Content is plain `.cfg` files under `Marketplace\Configs\<Feature>\`, any
filename, `[profile]` headers, comma-separated fields, hot-reloaded on save.
Bad lines are logged per entry with file and line; the rest still loads.
Only the physical NPC needs the in-game Marketplace Hammer (admin; Doug's
SteamID64 is in `MarketPlace.cfg` `OverrideDebug`).

`Marketplace\MarketPlace.cfg` changes: `UseLeaderboard = true`,
`AlwaysProgressServerTime = true`, `MarketTaxes = 1`, `Use Marketplace
Locally = true` (flip to false only once the server exists). Banker interest
off. `DistancedUI` lists filled but `Enabled = false`.

### Content pack (all `osrsheim_*.cfg`)

**Traders** (`Traders\`) — line = `cost item, amount, result item, amount`.
- `general_store`: buys basics at ~10x sell price (Wood 3c to FishingRod
  350c); sells wood, stone, hides 10-60c, trophies 5-200c, fish 3-50c.
- `gem_trader`: Amber 8, AmberPearl 20, Ruby 40, Crystal 20, Chain 60,
  SilverNecklace 80, GoldOre 120 (gems 25-45% of a kill's value); key forge
  `OSRS_LoopHalfKey, 1, OSRS_ToothHalfKey, 1 = OSRS_CrystalKey, 1`.
- `skillcape_shop`: every cape 5,000c, max cape 25,000c.
- `offerings` (`= true` discovery gate, Seeress): TrophyDeer 400, AncientSeed
  400, WitheredBone 150, GoblinTotem 500; a summon = 2.5-2.8x the boss purse.
  DragonEgg and DvergrKeyFragment wait on a wackydb dump. Fader, Kall never.
- `supplies` (`= true`, shopkeeper second menu): arrows and BoltCharred 20 a
  bundle, Flint 60c to Charred 400c; Wizardry eitr mead bases 60 / 150c,
  soups 20-90c, plates 30-120c. Vanilla bolts and mead bases need a dump.
  Meads 25-150c, cooked food 15-160c: the per-trip drain, never bought back.

**Bank** (`Bankers\`, profile `bank`): 134 bankable prefabs including ores
and metals.

**Gamblers** (`Gamblers\`): `dice_bag` 100c a roll (~5% house edge, prizes
coins 10-300, Ruby, Amber, Stone); `flower_poker` 1,000c (~11% edge, up to 3
queued rolls); `crystal_chest` 1 OSRS_CrystalKey a roll, 8 uniform prizes
(coins 200-1000, Ruby, AmberPearl, Crystal, Chain, SilverNecklace, GoldOre),
opened from the Gambler dialogue.

**Story quests** (`Quests\osrsheim_quests_free.cfg` 22 live + `osrsheim_quests_story.cfg`
57 staged in `staging\quest-pass\`, applied by `apply-quest-pass.ps1`; one-time via
cooldown 36500; ids OSRS-shaped, text Valheim lore; profile `lumbridge_guide`).
Types: Collect, Kill, Craft, Talk, Harvest (1). Per biome: a kill, a collect, a craft
of the tier's sword or shield (`Skill_EXP` on its skill 30-350), a fish quest
(`Skill_EXP: Fishing` 20-400), a boss kill (unlocks on the previous boss key, 300c
Eikthyr to 8,000c Kall). Talk intros to 3 NPCs. `Pet:` rewards: tame
Boar, Wolf (1 star), Lox. Coins 25c (Meadows) to 8,000c (Deep North), 107k total. Gated quests `= HiddenAnyCondition`
(hidden until open), chains `= HiddenOtherQuestCondition`. Six hull keel quests (§7), one keel each.

**Hunt contracts** (`Quests\osrsheim_quests_slayer.cfg`, 43 staged, `= Autocomplete`,
cooldown `60s`, biome boss key; profile `slayer_master`). Kills = coins: Meadows
Greylings 20 / Boars 15 = 80, Greydwarfs 30 = 150 + Amber, Skeletons 25 = 150 ·
Black Forest shamans 8 / brutes 5 = 200, Trolls 3 = 300 + Ruby · Swamp Leeches 15 =
250, Surtlings 10 = 300, Blobs 20 = 350, Draugr 25 = 400, Abomination 1 = 400 +
Ruby, Wraiths 3 = 500 · Mountain Drakes 10 = 500, Wolves 20 = 600, Fenrings 5 = 800
+ Ruby, Golems 3 = 900 + 2 Crystal · Plains Deathsquitoes 15 / shamans 5 = 700,
Fulings 25 / Lox 5 = 900, berserkers 2 = 1000 + Ruby · Mistlands Ticks 20 = 1200,
Seekers 20 = 1500, Gjall 2 = 1500 + SilverNecklace, soldiers 2 = 2000 + Ruby ·
Ashlands Twitchers 30 / Voltures 10 = 2000, Charred 20 / archers 15 = 2500, Morgen 3
= 3000 + 2 Ruby, Asksvin 5 = 3000, Bonemaw 1 = 4000 + GoldOre · Deep North Ulv 15 /
frozen skeletons 25 = 3000, Jotun warriors 5 = 4000 + GoldOre, Bjorn 3 = 4500 +
GoldOre, witches 3 = 4500 + 2 Ruby · starred (`creature, 1, 2`, superiors §12)
Greydwarf 500 + AmberPearl, Draugr 800, Wolf 1200, Fuling 1500, Seeker 2500 + Chain.
Skip fee (`QuestEvents\osrsheim_slayer_skip.cfg`, `OnCancelQuest: RemoveItem, Coins,
N`): a third of the pay.

**Prayers** (`Buffers\osrsheim_prayers.cfg`, profile `chapel`, 8-line
positional blocks): 7 buffs, 80c to 2,000c, 250-900 s (DamageReduction,
ModifyAttack, HealthRegen, StaminaRegen, RaiseSkills). Same group = mutually
exclusive. Buffs cannot be key-gated; price is the gate.

**Hiscores** (`LeaderboardAchievements\osrsheim_hiscores.cfg`, 23 entries):
kill milestones per biome, boss kill counts (1 and 10), The Knight's Sword
craft, explored 25/50/75%, first death, 100 deaths. IDs are case-sensitive.

**Info page** (`ServerInfos\osrsheim_guide.cfg`, `gielheim_guide`): the
in-game rulebook.

**Collection log** (`loot\collection-log.csv` -> `scripts\gen-collection-log.py`
-> `*\osrsheim_collection_log.cfg` in Quests, QuestProfiles, Dialogues;
`--check` / `--audit`, hook `scripts\collection-guard.py`): 137 Talk quests
`log_<prefab>` on Halla the Skald, unlock `HasItem, <prefab>, 1`, target the
same NPC, cooldown 36500, 1c, item kept. Dialogue pages per category list
each entry gated by `Condition: QuestFinished, log_<prefab>` (lit = found).
8 uniques, 7 elite uniques, 3 key parts, 6 keels, 8 pets, 24 capes, 7 gems,
5 shards, 69 trophies. Audit: every wackydb clone, drops.csv item and shard
needs a row.

**Dialogues** (`Dialogues\`, 20 nodes): one root per NPC; each root has an
`OpenUI, <Type>, <profile>` reply. If a reply opens nothing, use bare
`Command: OpenUI`. No commas inside reply text.

**Teleporters / Territories**: templates only, every line commented; fill
coordinates from the in-game `pos` command on Gielheim.

**Idle barks**: `Configs\RandomNpcSpeech.yml`, 5 sets (cosmetic).

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
| Gielheim Guide | Info | `gielheim_guide` | — | — |
| Halla the Skald | Quests | `collection_log` | `collection_log` | — |
| Kaupang | Marketplace | — | — | leaderboard tab lives here |

### Config audit (2026-09-21)
Evidence: `reference/config-audit-2026-09-21.json`; configs unchanged.
**Unfixed:** 138 Talk targets retain quotes in 10.0.1-beta.1; remove quotes,
preserve spaces; fix collection generator. Website example disagrees.
**Unfixed:** buff multipliers: attack 0.1/0.2 -> 1.1/1.2; health 0.5 -> 1.5;
stamina 0.3 -> 1.3; XP 0.1 -> 1.1. DamageReduction correct.
BetterUI tooltips true: EpicLoot requires false. Cooldown: bare days, `s` seconds.
Runtime unverified: icons/VFX, discovery gates, skip fee, fish quality,
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
  Configs = On`. The mod writes
  `warpalicious.More_World_Locations_TraderItems.yml` on first launch; Skill
  Books and Blacksmith Stones removed, trainer lists emptied (`.bak-generated`).
  `Use Custom Location YAML = On` extracts `..._LocationConfigs.yml` (188 MWL
  location types); locations bake at world-gen, so tune before Gielheim exists.

## 15. Server setup

- Flags (valheimgame.com/support/a-guide-to-dedicated-servers/): `-preset`,
  `-modifier combat|deathpenalty|resources|raids|portals <value>`, `-setkey`.
  Template: `scripts\server-start-template.bat`. Chosen: `-modifier
  deathpenalty casual`; `portals` undecided (keep vanilla: no metal).
- Deploy payload = the Gale profile root: `winhttp.dll`,
  `doorstop_config.ini` (relative target, works unchanged), `doorstop_libs\`,
  `BepInEx\`. Linux hosts use `start_server_bepinex.sh`.
- Same versions on host and both clients. ServerSync'd: all Smoothbrain
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

**Wiring session** (proves entries fire): `gen-loot.py --wiring`, validate,
launch, `devcommands`, `god`, `setkey defeated_bonemass`; spawn Greydwarf 3
(gems), Draugr_Elite 2 (Rare T2, key halves, unique), Eikthyr 1 (purse,
unique, pet), `setkey defeated_frozenking_p3` + JotunWarrior 1 3 (superior).
Then `gen-loot.py`, `dropthat:reload`, `removedrops`, `resetkeys`, Logout. Console takes synthetic typing only right after F5.

**Log reading**: `LogOutput.log` is the source of truth. Find the first
NullReferenceException and read down to the first frame that is not
UnityEngine / ObjectDB / ZNetScene. `MissingMethodException` on a Harmony
`DMD<...>` frame means a pre-1.0 plugin: scan plugin DLL MemberRefs for the
old signature (Valheim 1.0 `Character.Message` takes five args, pre-1.0
four). Item pickups log `Queue unlock msg` on first-ever pickup only.
`Removing orphan save file` is a red flag, not noise.

**Save safety**: 1.0 deletes a world whose main files are newer than its
`.ok.stmp`. Logout, wait for the save, then Quit.

**Vanilla names in no dump**: `grep -a` the `valheim_Data\StreamingAssets\SoftRef`
bundles (LZ4 keeps literals); that verified the nine `FishingBait*` ids.

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

## 18. Wave B and backlog

### Wave B settings (applied)

| Mod | Cfg file | Settings | Notes |
|---|---|---|---|
| OdinPlus PotionPlus | `com.odinplus.potionsplus.cfg` | `Lock Configuration = On`; wand, dragon staff, both hats `Crafting Station Level = 99` (uncraftable). Hellbroths stay (§6) | Skill `Alchemy` (= Herblore): 1 XP per craft at `opalchemy`; gain 1x / death loss 5% hard-coded. Stations `opalchemy`, `opcauldron`; base `Potion_Meadbase`. |
| Smoothbrain Exploration | `org.bepinex.plugins.exploration.cfg` | `Skill Experience Gain Factor = 0.5`, `Skill Experience Loss = 0`, `Treasure Multiplication Chance = 0` | Treasure doubling condition is inverted in source (fires at or below the level). Speed +15 / radius +250 at 100; cartography write 20 / read 40. All keys ServerSync. |
| JuJuz1 SkillGainModifier | `jujuz1.mods.skillgainmodifier.cfg` | `Logging Enabled = false`, `Duration = 50` (corpse-run seconds), `[Skill Gain] Global = 0.5`, `Fishing = 3` (a catch is ~2 XP; ~8,400 XP to 70 = ~1,400 catches), `[Skill reduction] Modifier = 0`; ships 2.5x, logging on, 60 s | Vanilla skills only; logging off or it errors per modded XP tick. No sync: same cfg on both clients. Per-skill keys under `[Skill Gain]` (0 = use Global). |
| Marlthon OdinShip | `marlthon.OdinShip.cfg` | `OSRS_Keel<Boss>:1:False` appended to the 7 hull `Crafting Costs`, War Ship takes Yagluth + Queen; everything else default, BepInEx writes the full file on first launch | Sections by display name, apostrophes stripped (`[Merchants boat]`); costs `Prefab:amount:recover`. Ship mats from the Carpenters Table. |
| sighsorry Trolling Fishing | `sighsorry.TrollingFishing.cfg` | `Lock Configuration = On`, `Fishing Bite Chance Bonus Factor = 0.3` (hook 10% at Fishing 0 to 30% at 100), `Fishing Extra Drop Chance Bonus Factor = 1` (bonus drops x2 at 100), `Fishing Rod Bag = Off`, `Fishing Rod Multi Line = Off` | ServerSync. Writes `TrollingFishing.yml` (bait each fish nibbles + chance) on first launch. |

### Planned, not done

- **Optional heavy content**: Therzie Warfare 1.9.2 + Armory 1.4.0 (fixed-stat
  boss-unique gear, needs Drop That wiring), Monstrum.
- **Ironman** is self-imposed (no marketplace, no trading; banker allowed).
  Hardcore Ironman = vanilla Hardcore modifier + delete on death.
- **Knobs to tune by feel**: skillcape price, gem prices, trophy prices,
  Slayer rewards, superior rarity (8% / 900 s), treasure map payout (1.5x),
  gambler edge, market tax, Goblin double coins, clone attack speeds, Fishing
  XP factor, fish sale prices, bite chance at 100,
  Wizardry Swamp-tier gear (reported strong; gate 20).

## 19. Dead ends

Almanac 3.7.94 (crashes on 1.0) · Boat mods: BoatAdditions, CustomShips (stale), Balrond shipyard (no cfg),
ValheimRAFT (freeform) · ReckonRunescape modpack (deprecated) · RtDItems defenders (cosmetic) ·
WackyEpicMMOSystem (single-level model) · EpicLoot affix drops on creature
tables (random rolls break fixed-item identity, the collection log, WIRSL tiers) · "DropThat Diversified Loot" Nexus
configs (deprecated) · EpicLoot as the loot pillar · altar
or resummon mods (bosses already resummon freely) · valheim.fandom.com (returns 402 to fetches;
use valheim.weirdgloop.org) · JewelHeim Marketplace Configs (never on 1.0).
Fishing: Hooked, PeasFishing (minigames) · Spearfishing (skips bait gates) ·
TheFisher · BetterFishing · FishingBonus · FishChum · Reely SpecTackleLure.

Magic mods rejected: MagicRevamp, MagicPlugin, Wisdom,
SecondaryAttacks, Jewelcrafting; dead on 1.0: ChebsNecromancy, RtDMagic,
MagicalMounts, MagicOverhaul, Skyheim.

## 20. Sources

- KG Marketplace: https://kg-marketplace.pages.dev/
- Spawn That: https://github.com/ASharpPen/Valheim.SpawnThat/tree/development/src/SpawnThat.Docs
- Drop That: https://github.com/ASharpPen/Valheim.DropThat/wiki (CharacterDrop-Configuration has `ConditionMinLevel`, `ConditionBiomes`)
- Dedicated server flags: https://www.valheimgame.com/support/a-guide-to-dedicated-servers/
- Gale: https://github.com/Kesomannen/gale · Hexium: https://valheim.hexium.gg
- Original plan export: `archive\2026-09-19-first-build\plan-artifact-export.txt`

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
`referenceerified-prefab-names.json` (Biome = BlackForest / Swamp /
Mountain / Plains / Mistlands, cape `Blackforest`); mages `GreydwarfMage_TW`
`SkeletonMage_TW` `FenringMage_TW` `GoblinMage_TW` `CorruptedDvergerMage_TW`
drop `Shard<Elder|Bonemass|Moder|Yagluth|Queen>_TW`. README misspells the
Mountain set (`_Mountains_`) and the stamina circlets (`_EitrRegen_`); the
json names are from the DLL. All five mages are `Spawn = Default` and appear
in no dump (every dump predates the 2026-09-20 install), so their spawn rates
are unreviewed. Mage purses + gem lists in
`loot\*.csv` (roamer class), names from the DLL until the next dump.

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
