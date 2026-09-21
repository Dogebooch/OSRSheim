@echo off
REM ============================================================================
REM  OSRSheim / Gielheim dedicated-server launch TEMPLATE (authored 2026-09-19)
REM  Copy this next to valheim_server.exe on the host (or paste the flags into the
REM  host panel's "additional arguments" box) and fill in every CHANGE_ME.
REM
REM  Flag syntax verified against Iron Gate's own guide on 2026-09-19:
REM    https://www.valheimgame.com/support/a-guide-to-dedicated-servers/
REM  -preset   : Normal, Casual, Easy, Hard, Hardcore, Immersive, Hammer
REM  -modifier : combat      veryeasy | easy | hard | veryhard
REM              deathpenalty casual | veryeasy | easy | hard | hardcore
REM              resources   muchless | less | more | muchmore | most
REM              raids       none | muchless | less | more | muchmore
REM              portals     casual | hard | veryhard
REM  -setkey   : nobuildcost | playerevents | passivemobs | nomap
REM  A modifier that is omitted stays at Normal/Default.
REM
REM  OSRSheim choices (see HANDOFF-TESTING.md "Server standup"):
REM    deathpenalty casual  = keep equipped gear, drop the inventory, 1% skill loss on the
REM                           vanilla skills (Smoothbrain skills are already at 0 loss).
REM                           Closest to OSRS "keep your 3 most valuable items".
REM    resources            = default 1x (locked decision).
REM    raids                = default. "more" is the knob for more OSRS-random-event chaos.
REM    portals              = UNDECIDED (plan: "per travel rule"). casual lets ore through.
REM    playerevents         = raids scale to each player's own boss progress; sensible for
REM                           two players who may split up. Optional.
REM
REM  MODDED SERVER: BepInEx must be on the host too. The deployable payload is the Gale
REM  profile root: winhttp.dll + doorstop_config.ini + doorstop_libs\ + BepInEx\ copied
REM  next to valheim_server.exe (check doorstop_config.ini target path is RELATIVE, not the
REM  Gale profile path). Then this .bat runs unchanged; doorstop injects on start.
REM  Linux hosts: use the profile's start_server_bepinex.sh instead.
REM  Doug's SteamID64 must be in <savedir>\adminlist.txt BEFORE first launch or
REM  devcommands / dropthat:reload / the Marketplace Hammer are unavailable.
REM ============================================================================
set SteamAppId=892970

echo Starting Gielheim...
valheim_server.exe -nographics -batchmode ^
  -name "Gielheim" ^
  -port 2456 ^
  -world "Gielheim" ^
  -password "CHANGE_ME_min_5_chars" ^
  -public 0 ^
  -savedir "CHANGE_ME_absolute_path" ^
  -saveinterval 1800 ^
  -backups 6 -backupshort 7200 -backuplong 43200 ^
  -modifier deathpenalty casual ^
  -setkey playerevents
