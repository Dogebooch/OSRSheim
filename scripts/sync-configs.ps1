<#
.SYNOPSIS
Sync BepInEx configs between the git repo (source of truth) and a Gale profile.

.DESCRIPTION
The repo's config\ is authoritative. The Gale profile and the dedicated host
are downstream copies that get overwritten.

  -Status   show what differs, change nothing (default)
  -Push     repo config\  ->  profile BepInEx\config\   (then run the validator)
            refused when origin/main has config\ commits this checkout lacks; -AllowBehind overrides
            -Solo sets KG 'Use Marketplace Locally = true' in the profile, for a world with no host
            (ModTest); a plain -Push puts the repo's false back, which joining the host needs
  -Pull     profile BepInEx\config\  ->  repo config\   (stage local edits)

Backups (*.bak*), mod-shipped examples and the KG binary asset folders are
never copied in either direction; they match .gitignore.

Neither direction deletes files. Extras on the destination are listed, not
removed, so a stray file in the profile can never silently delete authored
config and vice versa.

.EXAMPLE
Doug, after editing a cfg in the profile by hand:
  .\scripts\sync-configs.ps1 -Pull
  git add -A; git commit -m "Tune fishing bite chance"; git push

.EXAMPLE
Friend, picking up config changes mid-playthrough:
  git pull
  .\scripts\sync-configs.ps1 -Push

Windows blocks unsigned scripts by default. If it refuses to run, no need to
change any machine-wide setting - this bypasses it for that one run:
  powershell -ExecutionPolicy Bypass -File .\scripts\sync-configs.ps1 -Push

Python is not required on a second player's machine. Without it the push
still copies; it just skips the validator, which already ran before commit.

Most mods are ServerSync'd, so the host's values win at runtime and a stale
client cfg does not matter. The exceptions that DO need this push are
JuJuz1 SkillGainModifier (no sync) and the WackysDatabase / CLLC ymls, which
every client must have on disk. -Pull also regenerates reference\mods.tsv, the
committed mod manifest, so a Gale install or update lands with the configs.

.PARAMETER ProfilePath
Gale profile root. Defaults to the OSRSheim profile under %APPDATA%, so it
resolves correctly on either machine without editing this script.
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Push')][switch]$Push,
    [Parameter(ParameterSetName = 'Pull')][switch]$Pull,
    [Parameter(ParameterSetName = 'Status')][switch]$Status,
    [Parameter(ParameterSetName = 'Push')][switch]$AllowBehind,
    [Parameter(ParameterSetName = 'Push')][switch]$Solo,
    [string]$ProfilePath = (Join-Path $env:APPDATA 'com.kesomannen.gale\valheim\profiles\OSRSheim')
)

$ErrorActionPreference = 'Stop'

$RepoRoot   = Split-Path -Parent $PSScriptRoot
$RepoConfig = Join-Path $RepoRoot 'config'
$ProfConfig = Join-Path $ProfilePath 'BepInEx\config'

# Mirrors .gitignore. Keep the two in step.
$ExcludeFiles = @('*.bak', '*.bak-*', '*.bak.*', '*.cllc-example', '*.log', '*.log.*', '.gitkeep')
$ExcludeDirs  = @('Marketplace_CachedImages', 'Marketplace_KGChat_Emojis',
                  'Marketplace_Models', 'Marketplace_Sounds', 'Marketplace_VideoClips',
                  'Cache', 'wackyDatabase-BulkYML')

foreach ($p in @($RepoConfig, $ProfConfig)) {
    if (-not (Test-Path $p)) { throw "Not found: $p" }
}

function Invoke-Sync {
    param([string]$Source, [string]$Dest, [switch]$ListOnly)

    $args = @($Source, $Dest, '/E', '/FFT', '/NJH', '/NJS', '/NDL', '/NP')
    if ($ListOnly) { $args += '/L' }
    $args += '/XF'; $args += $ExcludeFiles
    $args += '/XD'; $args += $ExcludeDirs

    $out = & robocopy @args
    $code = $LASTEXITCODE
    # robocopy: 0 = nothing to do, 1-7 = copied/extra/mismatch, 8+ = failure
    if ($code -ge 8) { $out | Write-Host; throw "robocopy failed with exit code $code" }
    return ($out | Where-Object { $_ -match '\S' })
}

switch ($PSCmdlet.ParameterSetName) {
    'Push' {
        # The profile is shared by every worktree: a checkout behind origin/main on config\ would regress it.
        $behind = @()
        if (Get-Command git -ErrorAction SilentlyContinue) {
            try { & git -C $RepoRoot fetch -q origin main 2>$null } catch { }
            try {
                $behind = @(& git -C $RepoRoot log --oneline 'HEAD..origin/main' -- config 2>$null)
            } catch { Write-Host "Cannot compare with origin/main; pushing anyway." -ForegroundColor Yellow }
            if ($behind.Count -gt 0 -and -not $AllowBehind) {
                Write-Host "This checkout is behind origin/main on config\ ($($behind.Count) commit(s)):" -ForegroundColor Red
                $behind | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" }
                Write-Host "git merge origin/main, then re-run. -AllowBehind overrides." -ForegroundColor Red
                exit 1
            }
        }
        Write-Host "repo -> profile" -ForegroundColor Cyan
        Write-Host "  $RepoConfig"
        Write-Host "  $ProfConfig"
        Invoke-Sync -Source $RepoConfig -Dest $ProfConfig | Write-Host

        if ($Solo) {
            # true makes this PC run KG's server half too (bank, shops, quests); the headless host ignores it.
            $kg = Join-Path $ProfConfig 'MarketplaceAndServerNPCs.cfg'
            $text = [IO.File]::ReadAllText($kg)
            $pattern = '(?m)^Use Marketplace Locally = \w+'
            if ($text -notmatch $pattern) { throw "'Use Marketplace Locally' not found in $kg" }
            [IO.File]::WriteAllText($kg, ($text -replace $pattern, 'Use Marketplace Locally = true'))
            Write-Host "`nSolo: KG Use Marketplace Locally = true. A plain -Push resets it for the host." -ForegroundColor Cyan
        }

        $validator = Join-Path $PSScriptRoot 'validate-configs.py'
        $havePython = [bool](Get-Command python -ErrorAction SilentlyContinue)
        if ((Test-Path $validator) -and -not $havePython) {
            Write-Host "`nPython not found - skipping validate-configs.py." -ForegroundColor Yellow
            Write-Host "Fine on a second player's machine: the configs were validated before commit." -ForegroundColor Yellow
        }
        elseif (Test-Path $validator) {
            Write-Host "`nvalidate-configs.py" -ForegroundColor Cyan
            & python $validator
            if ($LASTEXITCODE -ne 0) {
                Write-Host "VALIDATOR FAILED - do not launch until this is clean." -ForegroundColor Red
                exit 1
            }
        }
        Write-Host "`nProfile updated. Host still needs its own deploy." -ForegroundColor Green
    }
    'Pull' {
        Write-Host "profile -> repo" -ForegroundColor Cyan
        Write-Host "  $ProfConfig"
        Write-Host "  $RepoConfig"
        Invoke-Sync -Source $ProfConfig -Dest $RepoConfig | Write-Host

        $genMods = Join-Path $PSScriptRoot 'gen-mods.py'
        if ((Test-Path $genMods) -and (Get-Command python -ErrorAction SilentlyContinue)) {
            Write-Host "`ngen-mods.py" -ForegroundColor Cyan
            & python $genMods
        }
        Write-Host "`nStaged in the working tree. Review with 'git diff', then commit." -ForegroundColor Green
    }
    default {
        Write-Host "Dry run, nothing written." -ForegroundColor Yellow
        Write-Host "`nWould copy repo -> profile:" -ForegroundColor Cyan
        Invoke-Sync -Source $RepoConfig -Dest $ProfConfig -ListOnly | Write-Host
        Write-Host "`nWould copy profile -> repo:" -ForegroundColor Cyan
        Invoke-Sync -Source $ProfConfig -Dest $RepoConfig -ListOnly | Write-Host
        Write-Host "`nRe-run with -Push or -Pull to apply." -ForegroundColor Yellow
    }
}

# robocopy's own exit codes (1-7 are successes) must not leak out as failures.
exit 0
