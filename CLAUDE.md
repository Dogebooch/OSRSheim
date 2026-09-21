# OSRSheim — Valheim 1.0 modded to play like Old School RuneScape

Two-player run. Doug maintains it with Claude and Codex (Codex reads
`AGENTS.md`, a pointer here). The AI's job is documentation upkeep and guided
walkthroughs; changes to the live profile are proposed as an exact file list
and walked through with Doug, not applied unprompted.

**Design principle:** OSRS gameplay loops and light grinds, Valheim lore and
feel. Copy OSRS mechanics (skills, gating, drop tables, Slayer, clues, bank).
Do not copy OSRS names, characters, items, quest text or audio; those are
OSRS-inspired but Valheim-flavoured. When in doubt, ask Doug.

- `RESEARCH.md` — the single reference: stack, every setting, every fact
  learned, testing knowledge, backlog. Update it when a fact is learned.
- `STATE.md` — what is live, what is next. Keep it under a page. Update it
  at the end of every session.
- `archive\` — first build's docs and config snapshot. Read-only.

## Where everything lives
- Gale profile **OSRSheim**: `%APPDATA%\com.kesomannen.gale\valheim\profiles\OSRSheim`
- Configs: the repo's `config\` is the source of truth. Edit there, run
  `scripts\sync-configs.ps1 -Push`, then deploy to the host. Profile and host
  are downstream: never edit them first, they get overwritten.
- Load log: `<profile>\BepInEx\LogOutput.log`. Prefab dumps: `<profile>\BepInEx\Debug\`.
- Game: `C:\Program Files (x86)\Steam\steamapps\common\Valheim`. Local saves:
  `%USERPROFILE%\AppData\LocalLow\IronGate\Valheim` (test worlds only).
- Pre-flight before any launch: `python scripts\validate-configs.py`.
- Full path table, doc URLs and console commands: `RESEARCH.md` §2, §16, §20.

## Documentation rules (strict)
- Less is more. Doug guides; the AI records.
- Edit in line. Fix the wrong line, delete the done line. Never append a status
  paragraph, changelog, history, or "why" section.
- Facts only: value, path, name. No explanations, no narrative.
- One fact per line. Prefer tables.
- Four root docs only: `CLAUDE.md`, `STATE.md`, `RESEARCH.md`, `AGENTS.md`. No
  new `.md` in the root. `archive\` is read-only.
- Size caps, hook-enforced (`scripts\doc-guard.py`): STATE 3 KB, CLAUDE 3.5 KB,
  AGENTS 0.8 KB, RESEARCH 40 KB. When a cap trips, prune before adding.
- Memory files follow the same rules. Cleanup pass only when Doug asks.

## Rules
- Mod list frozen until Gielheim exists: no installs. Pin mod versions in
  Gale; never mass-update. After a Valheim patch: BepInEx,
  then Jötunn, then mods one at a time, launching between each. Install
  updates through Gale, never by swapping DLLs.
- Loot cfgs are generated: edit `loot\*.csv`, run `python scripts\gen-loot.py`,
  never hand-edit `drop_that.character_drop*.cfg` (superiors: `update-superiors.py`).
  Enforced: IDs >= 100 (lists 110+/120+), vanilla drops never cleared,
  `ScaleByLevel = false`, <= 100 items per entry, no `DropOnePerPlayer` on purses.
- Collection log is generated: `loot\collection-log.csv` ->
  `gen-collection-log.py`; every collectible added or removed gets a row.
- Prefab names come only from the `BepInEx\Debug` dumps, EpicLoot's tables or
  a WackysDatabase dump. The validator enforces this.
- wackydb reads only `Item_*.yml`; never `wackydb_save_item` onto an authored file.
- Doug handles all Steam UI himself.
- Never kill valheim.exe with a world loaded (Valheim discards the save).
- Test on ModTest. The real world (Gielheim) is created on the host only after
  the stack is stable.
