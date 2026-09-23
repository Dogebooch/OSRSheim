# OSRSheim — Research and Build Reference

Section numbers are global: `§N` anywhere in the repo means the section below
or the topic file listed here. Read the hub, then only the topic file you need.

| § | File |
|---|---|
| 6, 8 | [`research\gating.md`](research/gating.md) |
| 7, 10, 12 | [`research\loot.md`](research/loot.md) |
| 11 | [`research\marketplace.md`](research/marketplace.md) |
| 18, 19 | [`research\backlog.md`](research/backlog.md) |
| 21 | [`research\wizardry.md`](research/wizardry.md) |

## 1. The build

Two players, rented dedicated server, 23 mods on Valheim 1.0.15. Skills grind to
100 at half speed; gear gated by skill level. Every creature pays coins and rolls
Gem/Rare tables; bosses drop uniques and pets, elites drop uniques and crystal-key
halves. EpicLoot: maps, bounties and the 15 unique Legendaries. KG Marketplace: shops, bank, gamblers,
quests, Slayer, prayers, hiscores, biome oaths.

## 2. Where things live

| Thing | Path |
|---|---|
| Mod manager | Gale, `C:\Program Files\Gale\gale.exe`, profile **OSRSheim** |
| Profile root | `C:\Users\drumm\AppData\Roaming\com.kesomannen.gale\valheim\profiles\OSRSheim` |
| Mod configs | repo `config\` is truth -> `<profile>\BepInEx\config\` |
| Load log | `<profile>\BepInEx\LogOutput.log`, appends (Unity copy: `...LocalLow\IronGate\Valheim\Player.log`) |
| Past session logs | `<profile>\BepInEx\Logs\LogOutput-<stamp>.log`, last 20, rotated by `launch-modded.ps1` |
| Prefab dumps | `<profile>\BepInEx\Debug\` (on world load) |
| Mod manifest (generated) | `reference\mods.tsv` (`scripts\gen-mods.py`) |
| Verified prefab names | `reference\verified-prefab-names.json` |
| Clone base dumps | `reference\wackydb-base-dumps\` |
| Vanilla prefab values (generated) | `reference\game-data\` (`scripts\extract-game-data.py`, needs UnityPy + TypeTreeGeneratorAPI) |
| Rate model | `scripts\rate-model.py`; in-game results in `reference\measured.csv` |
| World object counts | `scripts\count-world.py <world folder>` (1.0 chunked saves) |
| Modded launch without Gale | `scripts\launch-modded.ps1` |
| Server launch template | `scripts\server-start-template.bat` |
| Backups | `Desktop\Valheim-backup-2026-09-19`, `Desktop\OSRSheim-profile-backup-2026-09-19` |
| Sven's game | `F:\Steam\steamapps\common\Valheim` |

## 3. Mod stack

Frozen set. Versions: generated `reference\mods.tsv` (`gen-mods.py`), validator
checked. What is still untested in play: STATE. Sources: TS = Thunderstore, HX = Hexium (valheim.hexium.gg). Gale
reads both.

| Mod | Source | Role |
|---|---|---|
| BepInExPack Valheim (denikson) | TS | loader |
| Jötunn | TS | library |
| Smoothbrain Mining | TS | skill |
| Smoothbrain Lumberjacking | TS | skill |
| Smoothbrain Cooking | TS | skill |
| Smoothbrain Farming | TS | skill |
| Smoothbrain Blacksmithing | HX | skill |
| Smoothbrain Building | TS | skill |
| Smoothbrain Sailing | TS | skill |
| Smoothbrain Ranching | HX | skill |
| Smoothbrain Foraging | TS | skill |
| Smoothbrain Evasion | TS | skill |
| WackyItemRequiresSkillLevel (WIRSL) | TS | gear gating |
| WackysDatabase | TS | item clones, prefab dumps |
| Drop That | TS | creature + object loot |
| Spawn That | TS | superior spawns |
| CreatureLevelAndLootControl (CLLC) | TS | levels display, item yaml |
| EpicLoot | TS | treasure maps + bounties only |
| KG Marketplace (Marketplace And Server NPCs Revamped) | HX | economy, NPCs, quests |
| AzuExtendedPlayerInventory | HX | equipment tab + quick slots |
| XPortal | TS | named portals |
| More World Locations AIO | TS | towns and POIs |
| JsonDotNET / YamlDotNet | TS | dependencies |
| Therzie Wizardry | TS | magic ladder Black Forest to Mistlands |
| OdinPlus PotionPlus | TS | Herblore (Alchemy skill) |
| Smoothbrain Exploration | HX | Agility feel |
| JuJuz1 SkillGainModifier | TS | vanilla skill XP 0.5x |
| BetterUI_ForeverMaintained | TS | XP bar |
| sighsorry Trolling Fishing | TS | Fishing bite chance and bonus drops scale with skill (§18) |
| Marlthon OdinShip | TS | 7 hulls, keel-gated (§6, §7, §18) |
| JereKuusela Server devcommands | TS | admin console (§16) |

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
| Prayer | KG Buffer `chapel`, bones as cost (§11) |
| Runecraft, Thieving, Fletching, Firemaking | no analogue |

## 5. Skill settings (Smoothbrain)

Per-mod cfg `org.bepinex.plugins.<skill>.cfg`:

```
Skill Experience Gain Factor = 0.5
Skill Experience Loss = 0
```

Lumberjacking and Mining: `Skill Experience Gain Factor = 0.15` (rate model, pure
grind: level 40 ~11 h, 70 ~50-60 h). SkillGainModifier `Global` does not reach
Smoothbrain skills.

Evasion's keys are `Skill gain factor` / `Skill loss`. Skill caps default
(100). Vanilla world skill-gain modifier untouched. Vanilla skills: 0.5x via
SkillGainModifier `Global = 0.5`, death loss `Modifier = 0` (§18).

## 9. CLLC

`org.bepinex.plugins.creaturelevelcontrol.cfg`: `Maximum stars = None`,
`Loot system to be used = Vanilla`, `Lock Configuration = On`, `Use item
configuration yaml = On`. Effects and infusions left On (they only roll on
starred creatures, i.e. the superiors). Two-star creatures exist only through
Spawn That.

`ItemConfig.yml` (server-synced): `Coins` weight 0, stack 9999 (verified in
game); Amber, AmberPearl, Ruby weight 0.1 stack 100; SilverNecklace, Chain
weight 0.1 stack 50.

## 13. World, inventory, travel

- **More World Locations AIO**: `Enable Trainers = Off`, `Use Custom Trader
  Configs = On`, `Use Custom Location YAML = On`. First launch writes
  `..._TraderItems.yml` (Skill Books and Blacksmith Stones removed, trainer lists
  emptied) and `..._LocationConfigs.yml` (192 location types). Locations bake at
  world-gen: tune before Gielheim exists.
- `..._LocationConfigs.yml` is not in the repo; profile and host hold identical MWL defaults.
- MWL 5.1.1 null loot: `MWL_TreeTowers1` chest (all 10 entries) and one destructible,
  `MWL_MistTower2` tree drops. The host throws `DropTable.AddItemToList` NRE when TreeTowers1 spawns.

- **AzuEPI slots**: reserved `m_itemType`; `BlockCraft` not `BlockEquip`.

## 15. Server setup

- Flags (§20): `-preset`, `-modifier combat|deathpenalty|resources|raids|portals
  <value>`, `-setkey`, set in the panel's Additional Arguments. Chosen: `-modifier
  deathpenalty casual`; `portals` default, KG waystones are the travel reward,
  `CanTeleportWithOre = false` (§11).
- Host: GGServers Pterodactyl, BepInEx egg, 8 GiB. SFTP `d1228.ggn.io:2022`,
  key auth (panel Account > SSH Key). `sync-server.ps1 -Status|-Deploy|-Fetch` (host
  stopped; skips `Marketplace\SavedData`, `EpicLoot\BountySaves`, `KeyManager`,
  devcommands ymls). `tail-console.py`: console + power via `server.env`. The panel
  mod installer re-adds `plugins\*_ggs.dll` every start.
- MWL 5.1.1: if the root `_ggs` copy loads, the fallback `assetBundleManifest_Full` is
  missing on Linux: 259 errors. Fix: `_Full` copy beside `_full`.
- Drop That + Spawn That `Write*` dumps load every location prefab at boot (MWL on:
  10.6 GiB, 2.5 without). `sync-server.ps1` turns them off on the host.
- A client on the host takes the host's `false`: pre-sync dumps still write (drop tables,
  locations, local spawners), post-sync ones do not (character drops, loaded cfgs, world spawners).
- First join after a game launch: the client stalls 32-36 s (ServerSync configs, then
  world-gen setup); the host's 30 s `ZRpc timeout` drops it. Rejoin in the same session: 15-19 s.
- Host RAM: 2.54 GiB at boot, 4.01 GiB after one player flew 30 min (ZDOs 18k -> 201k); idle does not release it.
- `gen-mods.py --verify` checks host versions. ServerSync'd: Smoothbrain skills, CLLC,
  WIRSL, EpicLoot, AzuEPI, WackysDatabase, MWL, Trolling Fishing; Drop That clients
  pull the host's configs.
- Open: KG `Use Marketplace Locally = false`; `adminlist.txt` has `V_76561198092453267`
  only, add Doug (76561198855908341).
- Backups: host `worlds_local\` + Gale profile; stop via the panel.

## 16. Testing knowledge

**Console** (`-console`, F5): `devcommands`, `god`, `debugmode`, `spawn
<Prefab> <count> <level>` (3 = two stars), `killall`, `removedrops`,
`raiseskill <Skill> <n>`, `setkey` / `resetkeys`, `tod 0.9` / `tod -1`, `pos`,
`dropthat:reload`, `location Vendor_BlackForest` (disables saving).
`find <prefab>` counts world objects server-wide; `AlwaysAutoStack` merges, so it
counts stacks, a lower bound. `V` toggles auto-pickup (off before counting). An
admin client's `dropthat:reload` reloads the server and re-syncs (client log
`Unpacked CharacterDrop`). `killall` cannot kill bosses: CLLC 5.0.4 `PatchCharacterHit` calls
`GetAffixBoss(attacker)` unguarded, so any attacker-less hit on a boss throws;
boss-affix toggles do not help. Kill bosses by hand. Kills set `killedtroll` / `jotun_killed`; `removekey`.
On a server, drops follow the server's Drop That cfgs, not the local profile.
Computer-use screenshots mask Valheim; GDI `CopyFromScreen` captures it.
Synthetic right-clicks never reach Valheim (no build menu); keys and left-clicks do.
Typed text with spaces goes via clipboard and can drop focus: type words, send `space` as a key.

**Seen at shipping rates (server, 2026-09-22)**: 7 elite uniques, Rare T2-T4
key halves + riddle-stones, Gem T1 riddle-stone; `defeated_bonemass` necklace
gate holds.

**Seen at wiring (server, 2026-09-22)**: Rare T5, all 7 rows; superiors
`.200`-`.213` on all 8 rows + Meadows Troll; 1-star JotunWarrior drops no superior row.
Objects (`gen-objects.py --wiring`): Beech1 pet + Burl; MineRock_Copper pet + Geode + Amber;
MineRock_Iron AmberPearl; goldvein_frac pet + Geode + Ruby. Unseen: `SnowFirTree 2` (space breaks `spawn`).

**Segment count**: drop table with `SetDropMin/Max = 1`, `.0` = `Club`, other vanilla
indices `Enable = false`; `find Club` after the node. `spawn <item> 1 1 e` spawns and equips.
With a menu open, keys need a held press (0.15 s).

**Wiring session** (proves entries fire): `gen-loot.py --wiring`, validate,
launch, `devcommands`, `god`, `setkey defeated_bonemass`; spawn Greydwarf 3
(gems), Draugr_Elite 2 (Rare T2, key halves, unique), Eikthyr 1 (purse,
unique, pet), `setkey defeated_frozenking_p3` + JotunWarrior 1 3 (superior).
Then `gen-loot.py`, `dropthat:reload`, `removedrops`, `removekey` each key set, Logout
(`resetkeys` also wipes the world's own keys). Console takes synthetic typing only right after F5.
Server-only wiring: copy `config\` under a scratch `APPDATA` profile path, run
`gen-loot.py --wiring` with that `APPDATA`, copy the drop cfgs to the server; the Gale profile stays untouched.

**`ZNetScene.RemoveObjects` NRE every frame** (client on the host, 2026-09-22, fast debug
flight, 8 s after `GoblinCamp2` loaded): distant objects stop unloading, 15.8 GB, 4 FPS.
Relog clears it; no repeat on revisit.

**Post-build**: `scripts\post-build-check.py` - EOL against HEAD, clone ymls, csv
shape, gambler lines, repo/profile parity, validator.

**Stale-branch guard**: profile writers (`gen-loot`, `gen-objects`, `gen-collection-log`,
`update-superiors`, `sync-configs -Push`) refuse when origin/main has newer inputs.
Override: `--allow-behind` / `-AllowBehind`.

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
| Eikthyr dropped two trophies | `TrophyEikthyr` row in `drops.csv` on top of vanilla | row removed (6 kills, 6 trophies) |
| Roamer/elite gem odds 3-4x low | lists rolled at the list's class | lists roll at the creature's class |
| 7 elite uniques never loaded | Item yml without `m_weight` | dumped base weight; validator errors |
| `skill_none : 0 %` popup on every tree hit | axes still raise vanilla WoodCutting; Lumberjacking's `GetSkill(13)` returns a `None` dummy; BetterUI `XPNotification` prints it | accepted (cosmetic); only lever is `showXPNotifications = false` |

## 20. Sources

- KG Marketplace: https://kg-marketplace.pages.dev/
- Spawn That: https://github.com/ASharpPen/Valheim.SpawnThat/tree/development/src/SpawnThat.Docs
- Drop That: https://github.com/ASharpPen/Valheim.DropThat/wiki
- Dedicated server flags: https://www.valheimgame.com/support/a-guide-to-dedicated-servers/
- Gale: https://github.com/Kesomannen/gale · Hexium: https://valheim.hexium.gg
- kirilloid calculator: https://valheim.kirilloid.ru, data `src/data/` at https://github.com/kirilloid/valheim: default baseline for any time estimate without a measurement; cross-check for `rate-model.py` (no license, build unstated)
- Weirdgloop wiki: https://valheim.weirdgloop.org: spawn zones, creature spawners, damage/skill/stamina formulas, measured swing times
- Jötunn data: https://valheim-modding.github.io/Jotunn/data/intro.html: prefab names, vegetation list (1.0.7)
- valheim.source.gs: per-quality weapon damage, node HP, tool tiers (1.0.7, HTML only)
- Upgrade World (JereKuusela): `zones_generate`, `objects_count <ids> biomes=<b>`: whole-world density; not installed (mod freeze)
- Spawn That `spawn_that.cfg` `[Debug] PrintBiomeMap` / `PrintAreaMap`: zone biome map PNG in `BepInEx\Debug`
