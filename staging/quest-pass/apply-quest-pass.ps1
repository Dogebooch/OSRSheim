# Applies the 2026-09-21 quest pass to the Gale profile. Run from the repo root:
#   powershell -ExecutionPolicy Bypass -File staging\quest-pass\apply-quest-pass.ps1
# Copies 3 files, edits 4 files in place (backups *.bak-prequestpass), then runs the validator.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
$cfg  = Join-Path $env:APPDATA 'com.kesomannen.gale\valheim\profiles\OSRSheim\BepInEx\config\Marketplace\Configs'
$src  = Join-Path $PSScriptRoot 'Marketplace\Configs'
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Backup($p) { if (-not (Test-Path "$p.bak-prequestpass")) { Copy-Item $p "$p.bak-prequestpass" } }
function Edit-Lines($p, [scriptblock]$fn) {
    Backup $p
    $lines = [System.IO.File]::ReadAllLines($p)
    $out = & $fn $lines
    [System.IO.File]::WriteAllLines($p, [string[]]$out, $utf8)
    Write-Host "edited $p"
}

# 1. New / replaced files
foreach ($rel in 'Quests\osrsheim_quests_story.cfg', 'Quests\osrsheim_quests_slayer.cfg', 'QuestEvents\osrsheim_slayer_skip.cfg') {
    $dst = Join-Path $cfg $rel
    if (Test-Path $dst) { Backup $dst }
    Copy-Item (Join-Path $src $rel) $dst -Force
    Write-Host "copied  $rel"
}

# 2. Quest profiles: append the story ids to Ulfar's line, replace the Huntmaster's line
$storyIds = 'romeo_and_juliet, x_marks_the_spot, ernest_the_chicken, the_restless_ghost, druidic_ritual, animal_magnetism, misthalin_mystery, demon_slayer, haunted_mine, troll_stronghold, the_grand_tree, shades_of_mortton, the_dig_site, nature_spirit, in_search_of_the_myreque, shield_of_arrav, horror_from_the_deep, priest_in_peril, death_plateau, eagles_peak, mountain_daughter, between_a_rock, wolf_whistle, the_fremennik_isles, rag_and_bone_man, big_chompy_bird_hunting, my_arms_big_adventure, fight_arena, enlightened_journey, cold_war, tribal_totem, tai_bwo_wannai_trio, legends_quest, the_eyes_of_glouphrie, the_slug_menace, the_giant_dwarf, dream_mentor, the_path_of_glouphrie, swan_song, monkey_madness, tower_of_life, a_taste_of_hope, making_history, spirits_of_the_elid, sins_of_the_father, contact, enakhras_lament, dragon_slayer_ii, the_fremennik_exiles, royal_trouble, lunar_diplomacy, glorious_memories, desert_treasure_ii, the_lost_tribe, throne_of_miscellania, salt_in_the_wound, song_of_the_elves'
$huntIds = 'slayer_greyling, slayer_boar, slayer_greydwarf, slayer_skeleton, slayer_shaman, slayer_brute, slayer_troll, slayer_superior_greydwarf, slayer_draugr, slayer_blob, slayer_leech, slayer_surtling, slayer_wraith, slayer_abomination, slayer_superior_draugr, slayer_wolf, slayer_fenring, slayer_drake, slayer_golem, slayer_superior_wolf, slayer_fuling, slayer_lox, slayer_deathsquito, slayer_fuling_shaman, slayer_fuling_brute, slayer_superior_fuling, slayer_seeker, slayer_gjall, slayer_tick, slayer_seeker_soldier, slayer_superior_seeker, slayer_charred, slayer_morgen, slayer_twitcher, slayer_charred_archer, slayer_volture, slayer_asksvin, slayer_bonemaw, slayer_jotun, slayer_ulv, slayer_bjorn, slayer_jotun_witch, slayer_frozen_dead'
Edit-Lines (Join-Path $cfg 'QuestProfiles\osrsheim_quest_profiles.cfg') {
    param($lines)
    $lines | ForEach-Object {
        if ($_ -like 'cooks_assistant,*' -and $_ -notlike '*romeo_and_juliet*') { "$_, $storyIds" }
        elseif ($_ -like 'slayer_greydwarf,*') { $huntIds }
        else { $_ }
    }
}

# 3. Existing story quests: reward tweaks (exact whole-line matches)
$swap = @{
    'Item: Coins, 150 | Item: Bronze, 5'          = 'Item: Coins, 150 | Item: Bronze, 5 | Skill_EXP: Mining, 40'
    'Item: Coins, 400'                             = 'Item: Coins, 400 | Skill_EXP: Swords, 30'
    'Item: Coins, 3000'                            = 'Item: Coins, 2500 | Item: WolfPelt, 5'
    'Item: Coins, 150 | Skill_EXP: Fishing, 10'   = 'Item: Coins, 150 | Skill_EXP: Fishing, 20'
    'Item: Coins, 300 | Skill_EXP: Fishing, 20'   = 'Item: Coins, 300 | Skill_EXP: Fishing, 40'
    'Item: Coins, 800 | Skill_EXP: Fishing, 40'   = 'Item: Coins, 800 | Skill_EXP: Fishing, 60'
}
Edit-Lines (Join-Path $cfg 'Quests\osrsheim_quests_free.cfg') {
    param($lines)
    $lines | ForEach-Object { if ($swap.ContainsKey($_)) { $swap[$_] } else { $_ } }
}

# 4. Ulfar's help line and the rulebook
Edit-Lines (Join-Path $cfg 'Dialogues\osrsheim_dialogues.cfg') {
    param($lines)
    $lines | ForEach-Object { $_.Replace('sells capes to those who reach level 100.', 'sells capes to those who reach level 100. Take my boss contracts before you ring an altar.') }
}
Edit-Lines (Join-Path $cfg 'ServerInfos\osrsheim_guide.cfg') {
    param($lines)
    $lines | ForEach-Object {
        $_
        if ($_ -like '- Huntmaster Hrafn hands out*') { '- Ulfar the Guide gives one-time story quests for every biome. New ones appear as bosses fall. Take a boss contract before you ring the altar.' }
    }
}

# 5. Validate
python (Join-Path $root 'scripts\validate-configs.py')
