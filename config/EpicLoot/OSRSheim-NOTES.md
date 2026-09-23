# EpicLoot — OSRSheim customization notes

JSON cannot carry comments, so the record of what we changed lives here.

## 2026-09-19 — magic-item drops zeroed at the table level

**Problem.** `Global Drop Rate Modifier = 0` was set (line 76 of
`randyknapp.mods.epicloot.cfg`) but magic gear still dropped on ModTest
("Magic Wood Tower Shield", an epic "Cruel Shell" with 4 affixes). The mod's
own config comment explains why:

> "Elite creature and boss shard drops come from the loot tables directly and
> are not affected by this setting."

So the modifier was never going to cover what Doug saw. It scales normal loot;
elite and boss tables bypass it.

**Fix.** Edited `baseconfig/loottables.json` directly — the supported
customization path, named in EpicLoot's own README line 32 ("if you have
customized your loottables.json..."). For every table:

```
"Drops": [[0.0, 100.0]]
```

`Drops` is a list of `[numberOfItems, weight]` pairs, so a single
`[0, 100]` entry means "zero items, at weight 100" — a guaranteed no-drop.

- 141 top-level loot tables zeroed
- 157 `LeveledLoot` level entries zeroed
- verified afterwards: **0** entries can still roll an item

**What was deliberately NOT touched.**

- `ItemSets` (80) and `RestrictedItems` (12) — left intact; they only matter
  once something drops, and keeping them means the file still merges cleanly
  against a future EpicLoot update.
- `adventuredata.json` — untouched. Checked before editing: it contains no
  `LootTable`, `Loot` or `Drops` reference at all. Treasure maps pay out
  `ForestTokens` / `GoldTokens` / `IronTokens` / `Coins` per biome directly,
  and bounties pay `RewardCoins` (66 occurrences). **The clue-scroll and
  Slayer layer is completely independent of loot tables and still works.**
- `Adventure Mode Enabled = true` — unchanged, as designed.

**Side effect, accepted.** Shardstones also come from the loot tables
(README line 32), so they no longer drop either.

**Backup.** `baseconfig/loottables.json.bak-osrsheim` is the untouched
original.

**If EpicLoot updates.** It may prompt to refresh `baseconfig`. Accepting the
prompt restores vanilla loot tables and magic drops come back — re-run the
zeroing, or restore this file from the profile backup.

## Magic item sources (#108, 2026-09-23)

Magic items are found, never crafted. Replaces "EpicLoot restricted to clues + bounties".

| Source | Roll |
|---|---|
| `TreasureMapChest_<Biome>` | `Tier<N>Everything` entries carry the biome row below; `Drops` stays `[[0,100]]` until #107 |
| 2-star creatures (= superiors, bounty targets and adds) | `Tier0Mob`-`Tier9Mob` and `JotunWarrior` level 3: `Drops [[0,90],[1,10]]`, top-level `Drops []` |
| 15 OSRSheim uniques | unchanged (generated tables) |
| Enchanting table | `Enabled = false`, `Table Features Active = None` |

Rarity rows `[Magic, Rare, Epic, Legendary, Mythic, Ancient]`:

| Biome | Row | Tier tables |
|---|---|---|
| Meadows | 95, 5, 0, 0, 0, 0 | Tier0Mob |
| BlackForest | 85, 15, 0, 0, 0, 0 | Tier1Mob, Tier2Mob |
| Swamp | 75, 25, 0, 0, 0, 0 | Tier3Mob |
| Mountain | 70, 30, 0, 0, 0, 0 | Tier4Mob |
| Plains | 65, 34.5, 0, 0.5, 0, 0 | Tier5Mob |
| Mistlands | 55, 35, 9.5, 0.5, 0, 0 | Tier6Mob, Tier7Mob |
| AshLands | 45, 40, 14.5, 0.5, 0, 0 | Tier8Mob |
| DeepNorth | 40, 40, 19.5, 0.5, 0, 0 | Tier9Mob, JotunWarrior |

- EpicLoot rule (`LootRoller.GetDropsForLevel`): levels 1-3 read top-level `Drops`/`Loot` when non-empty, else `LeveledLoot`.
- 2-star creatures exist only through Spawn That and bounties, so one level-3 rate (10%) covers superiors; no separate 1% two-star rate. Bounty targets and adds roll it too (accepted).
- Drop That `.EpicLoot` modifiers do not apply to creature drops in this stack (§10).
- Legendary pick = weighted over matching `legendaries.json` entries + a generic legendary (weight 1, 4-6 random effects). Weight 0 on every vanilla legendary leaves only the generic one; weights unchanged. Set items off (`Set Item Drop Chance = 0`).
- `MagicEffectsCount` fixed: Magic 1, Rare 2, Epic 3, Legendary 4 (was 1-3 / 2-4 / 3-5 / 4-6); the OSRSheim uniques override it (`GuaranteedEffectCount = 1`).
- `magiceffects.json` `AddCarryWeight` `SelectionWeight 0` (was 5): carry weight comes from the torcs only (#17). Utility shard socket still grants +2 to +12 (`shardstones.json`).

## 2026-09-19 (late night) — adventure economy converted to coins (UNTESTED)

**Why.** With magic drops zeroed, the token economy still led straight back to
magic gear: treasure chests paid Forest/Iron/Gold tokens, and tokens bought
Haldor's gambles (random affixed items), runestones and shard materials. That
is the Diablo layer through a side door.

**What changed in `baseconfig/adventuredata.json`** (backup:
`adventuredata.json.bak-osrsheim`):

- `TreasureMap.BiomeInfo[*]`: all three token payouts set to 0 and `Coins` set
  to 1.5x the map's `Cost` (Meadows 100 -> 150 ... Deep North 800 -> 1200).
  A clue scroll is now a coin-positive treasure hunt, like a casket.
- `TreasureMap.SaleItems`: emptied (the six runestones).
- `Bounties.Targets[*]`: `RewardIron` and `RewardGold` set to 0; `RewardCoins`
  untouched (25 Meadows -> 800 Deep North). Slayer pays coin only.
- `Gamble`: all four gamble counts set to 0 (tab shows nothing to buy).
- `SecretStash`: `Materials` and `RandomItems` emptied; `OtherItems` keeps
  **Andvaranaut** at 1998 coins — the dowsing ring is the clue-scroll tool.

**Net effect.** Tokens never enter the economy, so every remaining magic-item
sink is unreachable without touching the sinks themselves. Coins are the only
adventure currency, matching the Drop That coin tables and the KG traders.

**Rollback.** Copy `adventuredata.json.bak-osrsheim` over `adventuredata.json`.
**If EpicLoot updates** and refreshes `baseconfig`, re-run the Python block in
STATE.md / HANDOFF-TESTING.md (it is idempotent).

## 2026-09-21 - bounties reworked: rare / hard / big (UNTESTED)

**Why.** Bounties and KG Slayer contracts were two menus paying coins for
kills. Split the roles: Slayer is the steady earner, a bounty is a rare
jackpot. Treasure maps were never redundant (they cost coins up front and
pay 1.5x - an exploration wager, not a kill contract).

**`randyknapp.mods.epicloot.cfg`** (backup `.bak-bounty-rework`):

| Key | Was | Now |
|---|---|---|
| `Gated Bounty Mode` | `Unlimited` | `BossKillUnlocksCurrentBiomeBounties` |
| `Enable Bounty Limit` | `false` | `true` |
| `Max Bounties Per Player` | `5` | `1` |

This reverses the 2026-09-19 decision that boss progression must not gate
bounty offers. It now matches how Slayer contracts are already gated (biome
boss key, RESEARCH.md 11).

**`baseconfig/adventuredata.json` `Bounties`** (backup `.bak-bounty-rework`):

| Key | Was | Now |
|---|---|---|
| `IronMinLevel` | 2 | 3 |
| `IronHealthMultiplier` | 2.0 | 3.0 |
| `GoldHealthMultiplier` | 3.0 | 4.5 |
| `AddsMinLevel` / `AddsMaxLevel` | 1 / 2 | 2 / 3 |
| `AddsHealthMultiplier` | 1.5 | 2.0 |
| `Targets[*].RewardCoins` | 25 - 800 | x6, 150 - 4800 |

`RewardIron` / `RewardGold` stay 0. Level 3 = 2 stars = the vanilla cap
(CLLC `Loot system = Vanilla`), so difficulty went into health and adds, not
more stars.

**Flat x6 was chosen** so the existing per-biome curve is preserved and one
number tunes the whole system. Resulting bounty vs the comparable Slayer
contract: Black Forest 450-540 vs 150-300, Swamp 900-1020 vs 350-400,
Mountain 1380-1800 vs 600-800, Plains 1740-2400 vs 900, Mistlands 3000-3300
vs 1500, Ashlands 3600-3900 vs 2500-3000, Deep North 4200-4800 vs 4000.
Early bounties are a 2-3x jackpot; late ones converge on Slayer.

**Rollback.** Copy both `.bak-bounty-rework` files back.

**Not throttleable.** EpicLoot exposes no "one bounty per N days" setting.
Scarcity here is boss gating + one in progress at a time + board reroll on
`RefreshInterval` (7 days). Whether an accepted bounty leaves the board
before the reroll is still unverified in game.
