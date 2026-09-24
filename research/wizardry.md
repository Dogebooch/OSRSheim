# OSRSheim research — Wizardry

§21 of the reference; hub and section map: [`RESEARCH.md`](../RESEARCH.md).

## 21. Wizardry (Therzie 1.2.0)

Cfg `Therzie.Wizardry.cfg`, ServerSync, `Lock Configuration = On`. Author
says delete the cfg on every update; re-apply the table below after
regenerating. No damage or eitr keys; balance = recipes.

| Edit | Value |
|---|---|
| All 7 pieces `Custom Build Category` | `Wizardry` (was `Warfare`) |
| 9 potions `Custom Crafting Station` | `opalchemy` (was `PotionCauldron_TW`) so they give Alchemy XP |
| Skillful potion (`PotionSkills_TW`) `Crafting Station` | `Disabled`: +8 all skills passed WIRSL craft gates |
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
| Buy for coins | the `supplies` prices are in §11: mead bases, soups, plates, the 4 buff scrolls, 2 world-picked mushrooms |
| Never sold | shards, staves, spellslinger pieces, circlets, rings, biome scrolls — coins must not skip a WIRSL gate or the mage hunt |

Buff scrolls `ArcaneScroll_<DamageBuff|JumpBuff|SlowfallBuff|SpeedBuff>_TW`
are terminal consumables; biome scrolls `ArcaneScroll_<Biome>_TW` are the
upgrade material and are never sold.
