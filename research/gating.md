# OSRSheim research — Gear gating and custom items

§6, §8 of the reference; hub and section map: [`RESEARCH.md`](../RESEARCH.md).

## 6. Gear gating (WIRSL)

File: `WackyMole.ItemRequiresSkillLevel.yml`. Top-level `Requirements:` list;
each entry is `PrefabName` + a `Requirements` list of `Skill`, `Level`,
`BlockCraft`, `BlockEquip`. Log line on load: `ItemRequiresSkillLevel Loaded:
338`. A wrong PrefabName fails OPEN with no log line. Tiers:
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
| Ashlands (flametal) | 55 weapons, 60 armor craft | |
| Deep North | 60 weapons, 65 armor craft | |

**Weapon skill at biome entry** (`sim-run.py`, median main-family level = the Swords curve, 400 runs)

| Biome | Gate | Balanced | Fighter | Balanced reaches gate |
|---|---|---|---|---|
| Black Forest | 15 | 12 | 14 | 22 h |
| Swamp | 20 | 28 | 34 | 30 h |
| Mountains | 30 | 39 | 48 | 53 h |
| Plains | 40 | 44 | 54 | 90 h |
| Mistlands | 50 | 48 | 58 | 218 h (33 h in) |
| Ashlands | 55 | 53 | 63 | 262 h (17 h in) |
| Deep North | 60 | 60 | 72 | 308 h (at entry) |

Combat index vs vanilla at entry 0.92-1.04 (`sim-run.py`). Skill roll spread ±15%. `Global = 0.5` kept; fallback lever: per-weapon `[Skill Gain]` keys (semantics unverified).

**Skill split**

- Weapons: their weapon skill.
- Armor, capes, circlets, trinkets (15 in 1.0): CRAFT on Blacksmithing at
  tier, equip ungated. Shields: EQUIP on Blocking + CRAFT on Blacksmithing.
  Blocking: bronze/bone 15, iron/serpent 20, silver 25, blackmetal 30, carapace 30, flametal 35, gold/roots 40.
- Picks: Mining 10 / 20 / 40. One-hand axes: Lumberjacking 15 / 20 / 35 (BlackMetal) / 40
  (JotunBane) / 45 (Gold). Battleaxes and Berzerkr stay on Axes.
- Staves: ElementalMagic / BloodMagic at 50 / 55 / 60, craft and equip.
  Wizardry: `StaffBlackforest_TW`, `StaffSurtling_TW` ungated, `StaffSwamp_TW` 20,
  `StaffMountain_TW` 30, `StaffPlains_TW` 40 and `StaffGolem_TW` Blood 40,
  `StaffMistlands_TW` 50. Spellslinger sets and circlets 15 / 20 / 30 / 40 /
  50 on the armor split. Rings craft Blacksmithing 15 / 20 / 30 / 40 / 50, equip ungated.
- Unarmed ladder 30 / 40 / 60.
- Crossbows: Arbalest ungated, Ripper 20, Gold 30.
- Skillcapes: skill 100; Herblore cape Alchemy + Foraging; max cape ANDs all 24 skills. Bought only at 100 (Verdandi).
- Uniques also need their biome's oath: a second requirement element `GlobalKeyReq: oath_<biome>` (a key element
  returns on the key alone, so it cannot share the skill element).
- Gem-tipped bolts: Amber 10, Pearl 20, Ruby 25, Crystal 30 on Crossbows (crossbow tier; craft + shoot).
- Skill guide: `gen-handbook.py` lists every gate, Smoothbrain level perk and `SkillMore` quest per skill level.
- Hellbroths (broth + charge, craft + use): Alchemy 10 Flames, 15 Eternal
  Life, 30 Frost, 40 Thors Fury. Names `Hellbroth_of_<X>` in the 2026-09-21 load log;
  `_Charge` from the DLL only.
- Alchemy brews (craft + use): Medium flasks 10, Grands 20, Stealth 25,
  Magelight + Weapon Oil 30, Fortification + Second Wind 35, Elements 40,
  Gods 50, the 4 Philosopher's Stones 60 (cfg factor 1 = x2 XP). Lesser vials ungated.
- Uniques (gate = sim family-main level at the first drop, rounded up to 5; `sim-run.py` uniques): DragonAxe Lumberjacking 30,
  DragonfireShield Blocking 35, BandosGodsword Swords 50, AbyssalWhip Swords 55,
  ScytheOfVitur Polearms 70; DraugrVisage ungated (armor). Elite: HillGiantClub Clubs 30,
  RuneScimitar Swords 35, GraniteMaul Clubs 45, DragonHalberd Polearms 50, CrystalBow Bows 65 (bow main x1.5 XP),
  AbyssalBludgeon Clubs 65, DragonBattleaxe Axes 65.
- Fishing (bait, craft + equip):
  `FishingBaitForest` 10 Trollfish · `Swamp` 20 Giant herring · `Ocean` 25 Tuna,
  Coral cod · `Cave` 30 Tetra · `Plains` 40 Grouper · `Mistlands`
  45 Pufferfish, Anglerfish · `Ashlands` 50 Magmafish · `DeepNorth` 55 Northern
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
`GlobalKeyReq` without WAP = `ZoneSystem.CheckKey(key, GameKeyType.Player)`: the player's own key (KG `AddPlayerKey`).
Staff skill = game-data `m_skillType` (9 Elemental, 10 Blood): GreenRoots, ThunderBlood Elemental; FrostOrbs, OrbofAhri Blood.
**Unverified:** skill name `Alchemy`.

## 8. Custom items (WackysDatabase)

Folders: `wackysDatabase\Items\Item_OSRS_*.yml`, `Recipes\Recipe_*.yml`, `Pieces\Piece_<prefab>.yml` (needs `piecehammer`). Base dumps:
`reference\wackydb-base-dumps\`. `Primary_Attack:` needs a `Secondary_Attack:`
block: wackydb dereferences it unguarded and drops the rest of the item's data.
Every yml needs a top-level `m_weight` or wackydb drops it (validator checks).

- 8 boss uniques (table above). Stat twists: Abyssal Whip = Mistwalker clone,
  frost stripped, slash 104, stamina 14, attack speed 1.2; Bandos Godsword
  attack speed 0.9; Scythe of Vitur 0.95.
- 12 pets = trophy clones (8 boss, + Mining and Woodcutting on rocks and trees, §7, + Fishing and Farming from skilling contracts, §11); 2 curios = Amber clones, 1/500, sold to the gem trader 35c.
- 8 trimmed oath capes (CapeDeepNorth), 4 saga-rank cosmetics, 4 vanity cloaks (bought, not logged), 4 gem-tipped bolts.
- 7 elite uniques + 3 hoard key parts (§7).
- 4 riddle-stones (AncientGemstone clones) + 6 rewards (4 capes, 2 helmets): armor 0,
  `SE_Equip` and `SE_SET_Equip` `EffectName: delete` (also saga cosmetics), no modifiers, no WIRSL gate, AzuEPI vanity-wearable.
- 24 skillcapes = CapeLinen clones, display `<Valheim skill> cape`, one per skill in
  the §4 table plus `Allfather's cape` (all 23 at 100); equip-gated at 100, no recipe,
  sold by Verdandi only at 100 (dialogue). Skillcapes and 8 oath capes: stats stripped like the riddle rewards.
- 6 jewellery = ring/amulet clones, Trinket, gem recipes, Bsmith 15-50, `m_value: 0`.
- Jewellery SEs clone `SetEffect_TrollArmor` (Sneak +15: `m_skillLevel: 101`, `m_skillLevelModifier: 15`); `m_skillLevelModifier: 0` strips it, Nightstep keeps it.
- `m_stealthModifier` scales the crouched detection range (`range × stealthFactor`): negative = stealthier.
- One finger slot (`$azuepi_fingerslot`) holds 3 OSRS rings + 5 Wizardry rings (AzuEPI compat) + EpicLoot `Andvaranaut` (Secret Stash) and `GoldRubyRing`/`SilverRing` (no live source: forge recipes off, loot set `ModUtility` unused). Wizardry rings: Utility type, armor 10, craft Blacksmithing (BlockEquip false), ArcaneAnvil_TW:

| Ring | Effect | Bsmith | Anvil | Shard |
|---|---|---|---|---|
| `RingBlackForest_TW` | Sneak +5 | 15 | 1 | Elder 4 |
| `RingSwamp_TW` | ElementalMagic +3 | 20 | 2 | Bonemass 4 |
| `RingMountain_TW` | eitr regen +4% | 30 | 3 | Moder 4 |
| `RingPlains_TW` | ElementalMagic damage +3% | 40 | 4 | Yagluth 4 |
| `RingMistlands_TW` | BloodMagic +7 (English description: +5), health regen +2% | 50 | 4 | none |
- Vanilla traders (Haldor, Hildir, Bog Witch) buy any item with `m_value > 0` at `m_value x stack`; a clone without `m_value` keeps its source's. Crafted items stay `m_value: 0`.

Clones register and load from cache before world load and drop off kills. Both server and every client need the yml files.
