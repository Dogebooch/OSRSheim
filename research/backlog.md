# OSRSheim research — Backlog and dead ends

§18, §19 of the reference; hub and section map: [`RESEARCH.md`](../RESEARCH.md).

## 18. Wave B and backlog

### Wave B settings

| Mod | Cfg file | Settings | Notes |
|---|---|---|---|
| OdinPlus PotionPlus | `com.odinplus.potionsplus.cfg` | `Lock Configuration = On`; wand, dragon staff, both hats `Crafting Station Level = 99`. Hellbroths stay (§6) | Skill `Alchemy` (= Herblore) on the vanilla curve `(L+1)^1.5*0.5+0.5` per level: 76 XP to 10, 2107 to 40, 20301 to 100. 1 XP per craft at a station named `opalchemy*`, nothing else: `opcauldron` is a plain CraftingStation (4.3.4 bundle: no Incinerator, the lever is a mesh), so `Potion_Meadbase` pays 0 XP. Crops grow 4000-5000 s at Farming 0, divided by `1 + skill*(Grow Speed Factor 3 - 1)` (22-28 min at 100). Philosopher's Stone is ADDITIVE (`SE_Stats.ModifyRaiseSkill`), Alchemy only: cfg 2.0 = 3x. Chain and gates: `scripts\check-alchemy-balance.py`. |
| Smoothbrain Exploration | `org.bepinex.plugins.exploration.cfg` | `Skill Experience Gain Factor = 0.5`, `Skill Experience Loss = 0`, `Treasure Multiplication Chance = 0` | Treasure doubling condition is inverted in source. Speed +15 / radius +250 at 100; cartography write 20 / read 40. All keys ServerSync. |
| JuJuz1 SkillGainModifier | `jujuz1.mods.skillgainmodifier.cfg` | `Logging Enabled = false`, `Duration = 50` (corpse-run seconds), `[Skill Gain] Global = 0.5`, `Fishing = 3`, `[Skill reduction] Modifier = 0` | Vanilla skills only; logging off or it errors per modded XP tick. No sync: same cfg on both clients. Per-skill keys under `[Skill Gain]` (0 = use Global). |
| Marlthon OdinShip | `marlthon.OdinShip.cfg` | `OSRS_Keel<Boss>:1:False` appended to the 7 hull `Crafting Costs`, War Ship takes Yagluth + Queen; everything else default, BepInEx writes the full file on first launch | Sections by display name, apostrophes stripped (`[Merchants boat]`); costs `Prefab:amount:recover`. Ship mats from the Carpenters Table. PieceManager resolves costs at ObjectDB.Awake, before wackydb adds clones, and drops a missing item silently; re-resolves only on a `Crafting Costs` change. Hull costs restated in `wackysDatabase\Pieces\` (validator: must match). |
| sighsorry Trolling Fishing | `sighsorry.TrollingFishing.cfg` | `Lock Configuration = On`, `Fishing Bite Chance Bonus Factor = 0.3`, `Fishing Extra Drop Chance Bonus Factor = 1`, `Fishing Rod Bag = Off`, `Fishing Rod Multi Line = Off` | ServerSync. Writes `TrollingFishing.yml` (bait each fish nibbles + chance) on first launch. |

### Planned

- **Optional heavy content**: Therzie Warfare 1.9.2 + Armory 1.4.0, Monstrum.
- **Ironman** is self-imposed (no marketplace, no trading; banker allowed).
- **Knobs to tune by feel**: skillcape price, gem prices, trophy prices,
  Slayer rewards, superior rarity (0.03% / 900 s, MaxSpawned 10, `update-superiors.py`), treasure map payout (1.5x),
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
