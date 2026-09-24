# OSRSheim — Valheim 1.0 modded to play like Old School RuneScape

Two-player run. Doug maintains it with Claude and Codex (Codex reads
`AGENTS.md`, a pointer here). The AI's job is doc upkeep and guided
walkthroughs; live-profile changes are proposed as an exact file list and
walked through with Doug, not applied unprompted.

**Design principle:** OSRS gameplay loops and light grinds, Valheim lore and
feel. Copy OSRS mechanics (skills, gating, drop tables, Slayer, clues, bank).
Do not copy OSRS names, characters, items, quest text or audio; those are
OSRS-inspired but Valheim-flavoured. When in doubt, ask Doug.

**Balance:** each biome fights, gears and pays like vanilla, as if Iron Gate
had built it this way; only total playtime grows. Skill gates unlock new
things to do (magic, abilities, rares), not bigger numbers. Test: would Iron
Gate ship it? Run: ~375 h to 70 (back-loaded); 70-100 optional (#81).

**Rares:** small power over their tier, never a stat stick. Each one:
1. drops before its skill gate is reached (the gate times it, not the biome);
2. does one thing no other item does (effect, special, utility);
3. stays useful into the next biome;
4. is rare and visible (beam, collection log).

- `RESEARCH.md` — reference hub; topic files in `research\` (section map at
  its top, §N global). Update the file that owns the section when a fact is learned.
- `STATE.md` — what is live, what is next. Under a page. Update it every
  session.
- `README.md` — what OSRSheim is, repo map, glossary. No status.
- `archive\` — first build's docs and config snapshot. Read-only.

## Where everything lives
- Gale profile **OSRSheim**: `%APPDATA%\com.kesomannen.gale\valheim\profiles\OSRSheim`
- Configs: the repo's `config\` is the source of truth. Edit (and generate) there, run
  `scripts\sync-configs.ps1 -Push`; Sven deploys to the host. Profile and host
  are downstream: never edit them first, they get overwritten.
- Load log: `<profile>\BepInEx\LogOutput.log`. Prefab dumps: `<profile>\BepInEx\Debug\`.
- Game: `C:\Program Files (x86)\Steam\steamapps\common\Valheim`. Local saves:
  `%USERPROFILE%\AppData\LocalLow\IronGate\Valheim` (test worlds only).
- Pre-flight: `post-build-check.py` (`watch.py` runs it).
- Full path table, doc URLs and console commands: `RESEARCH.md` §2, §16, §20.

## Documentation rules (strict)
- Less is more. Doug guides; the AI records.
- Edit in line. Fix the wrong line, delete the done line. Never append a status
  paragraph, changelog, history, or "why" section.
- Facts only: value, path, name. No explanations, no narrative.
- One fact per line. Prefer tables.
- Five root docs only: `CLAUDE.md`, `STATE.md`, `RESEARCH.md`, `AGENTS.md`,
  `README.md`. No new `.md` in the root. `research\` holds only the files in
  the hub map. `archive\` is read-only.
- Size caps, hook-enforced (`scripts\doc-guard.py`): STATE 3.5 KB, CLAUDE 4.5 KB,
  README 5 KB, AGENTS 0.8 KB. RESEARCH and `research\` uncapped. Prune in place when a cap trips.
- Memory files follow the same rules. Cleanup pass only when Doug asks.

## Rules
- Mod list frozen until Gielheim exists: no installs
  (exceptions: #46 Quick Stack Store, #124 WEC). Pin mod versions in
  Gale; never mass-update. After a Valheim patch: BepInEx,
  then Jötunn, then mods one at a time, launching between each. Install
  updates through Gale, never by swapping DLLs.
- Generated, never hand-edited: `drop_that.character_drop*.cfg` from `loot\*.csv`
  (`gen-loot.py`; superiors `update-superiors.py`), the collection log from
  `loot\collection-log.csv` (`gen-collection-log.py`; every collectible gets a
  row), `reference\mods.tsv` from the profile (`gen-mods.py`),
  `drop_that.drop_table.cfg` from `loot\objects.csv` (`gen-objects.py`).
  Enforced: IDs >= 100 (lists 110+/120+), vanilla drops never cleared,
  `ScaleByLevel = false`, <= 100 items per entry, no `DropOnePerPlayer` on purses.
- Prefab names come only from the `BepInEx\Debug` dumps, EpicLoot's tables or
  a wackydb dump. Validator-enforced.
- wackydb reads only `Item_*.yml`; never `wackydb_save_item` onto an authored file.
- Doug handles all Steam UI himself.
- Never kill valheim.exe with a world loaded (Valheim discards the save).
- Time and rate estimates come from `scripts\rate-model.py`: `reference\measured.csv`
  > model > kirilloid; name the source. New checks: `parse-hits.py`.
- Test on ModTest. The real world (Gielheim) is created on the host only after
  the stack is stable.
