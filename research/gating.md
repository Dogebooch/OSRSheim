# OSRSheim research — Gear gating and custom items

§6, §8 of the reference; hub and section map: [`RESEARCH.md`](../RESEARCH.md).

## 6. Gear gating (WIRSL)

File: `WackyMole.ItemRequiresSkillLevel.yml`. Top-level `Requirements:` list;
each entry is `PrefabName` + a `Requirements` list of `Skill`, `Level`,
`BlockCraft`, `BlockEquip`. Log line on load: `ItemRequiresSkillLevel Loaded:
331`. A wrong PrefabName fails OPEN with no log line. Tiers:
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

**Weapon skill at biome entry** (`rate-model.py ladder`, one weapon skill, 25% of play fighting at 100 kills/hr; #83)

| Biome | Gate | OSRSheim | Vanilla | Damage vs vanilla |
|---|---|---|---|---|
| Black Forest | 15 | 28 | 24 | +4% |
| Swamp | 22 | 38 | 32 | +6% |
| Mountains | 30 | 49 | 42 | +6% |
| Plains | 40 | 56 | 48 | +7% |
| Mistlands | 50 | 64 | 55 | +7% |
| Ashlands | 60 | 74 | 64 | +8% |
| Deep North | 70 | 86 | 74 | +9% |

50% fighting: +5% to +9%. Skill roll spread ±15%. `Global = 0.5` kept; fallback lever: per-weapon `[Skill Gain]` keys (semantics unverified).

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
  50 on the armor split. Rings craft Blacksmithing 15 / 20 / 30 / 40 / 50, equip ungated.
- Unarmed ladder 30-70.
- Crossbows: Arbalest ungated, Ripper 20, Gold 30.
- Skillcapes: skill 100; Herblore cape Alchemy + Foraging; max cape ANDs all 24 skills.
- Hellbroths (broth + charge, craft + use): Alchemy 10 Flames, 15 Eternal
  Life, 30 Frost, 40 Thors Fury. Names `Hellbroth_of_<X>` in the 2026-09-21 load log;
  `_Charge` from the DLL only.
- Alchemy brews (craft + use): Medium flasks 10, Grands 20, Stealth 25,
  Magelight + Weapon Oil 30, Fortification + Second Wind 35, Elements 40,
  Gods and the 4 stones 50. Lesser vials ungated.
- Uniques (#86: damage and gate half a tier above the drop biome, capped at 70): DragonAxe Lumberjacking 18,
  DragonfireShield Blocking 35, BandosGodsword Swords 45, AbyssalWhip Swords 55,
  ScytheOfVitur Polearms 70; DraugrVisage ungated (armor). Elite: HillGiantClub Clubs 18,
  RuneScimitar Swords 27, GraniteMaul Clubs 35, DragonHalberd Polearms 45, CrystalBow Bows 55,
  AbyssalBludgeon Clubs 65, DragonBattleaxe Axes 70.
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

WIRSL 1.4.7 (`Patches.cs`): an unknown skill name is unmet (fails closed); the level read is
`GetSkillLevel`, buffs included (Wizardry Skillful potion +8 all skills, 15 min).
**Unverified:** skill name `Alchemy`. Which skill each vanilla staff uses
(`StaffOrbofAhri`: wikis disagree); check `m_skillType` in a wackydb dump.

## 8. Custom items (WackysDatabase)

Folders: `wackysDatabase\Items\Item_OSRS_*.yml`, `Recipes\Recipe_*.yml`, `Pieces\Piece_<prefab>.yml` (needs `piecehammer`). Base dumps:
`reference\wackydb-base-dumps\`. `Primary_Attack:` needs a `Secondary_Attack:`
block: wackydb dereferences it unguarded and drops the rest of the item's data.
Every yml needs a top-level `m_weight` or wackydb drops it (validator checks).

- 8 boss uniques (table above). Stat twists: Abyssal Whip = Mistwalker clone,
  frost stripped, slash 104, stamina 14, attack speed 1.2; Bandos Godsword
  attack speed 0.9; Scythe of Vitur 0.95.
- 10 pets = trophy clones (8 boss, + Mining 1/300,000 a segment, Woodcutting
  1/16,000 a tree, §7); 2 curios = Amber clones, 1/500, sold to the gem trader 35c.
- 7 elite uniques + 3 crystal key parts (§7).
- 4 riddle-stones (AncientGemstone clones) + 6 rewards (4 capes, 2 helmets): armor 0,
  no `SE_Equip` or modifiers, no WIRSL gate, AzuEPI vanity-wearable.
- 24 skillcapes = CapeLinen clones, display `<Valheim skill> cape`, one per skill in
  the §4 table plus `Allfather's cape` (all 23 at 100); equip-gated at 100, no recipe,
  sold by the skillcape shop. Skillcapes and 8 oath capes: stats stripped like the riddle rewards.
- 6 jewellery = ring/amulet clones, Trinket, gem recipes, Bsmith 15-50, `m_value: 0`.
- Jewellery SEs clone `SetEffect_TrollArmor` (Sneak +15: `m_skillLevel: 101`, `m_skillLevelModifier: 15`); `m_skillLevelModifier: 0` strips it, Nightstep keeps it.
- `m_stealthModifier` scales the crouched detection range (`range × stealthFactor`): negative = stealthier.
- One finger slot (`$azuepi_fingerslot`) holds 3 OSRS rings + 5 Wizardry rings (AzuEPI compat) + EpicLoot `Andvaranaut` (Secret Stash) and `GoldRubyRing`/`SilverRing` (magic drops; forge recipes off). Wizardry rings: Utility type, armor 10, craft Blacksmithing (BlockEquip false), ArcaneAnvil_TW:

| Ring | Effect | Bsmith | Anvil | Shard |
|---|---|---|---|---|
| `RingBlackForest_TW` | Sneak +5 | 15 | 1 | Elder 4 |
| `RingSwamp_TW` | ElementalMagic +3 | 20 | 2 | Bonemass 4 |
| `RingMountain_TW` | eitr regen +4% | 30 | 3 | Moder 4 |
| `RingPlains_TW` | ElementalMagic damage +3% | 40 | 4 | Yagluth 4 |
| `RingMistlands_TW` | BloodMagic +7 (English description: +5), health regen +2% | 50 | 4 | none |
- Vanilla traders (Haldor, Hildir, Bog Witch) buy any item with `m_value > 0` at `m_value x stack`; a clone without `m_value` keeps its source's. Crafted items stay `m_value: 0`.

Clones register and load from cache before world load and drop off kills. Both server and every client need the yml files.
