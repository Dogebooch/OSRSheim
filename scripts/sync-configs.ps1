<#
.SYNOPSIS
Sync BepInEx configs between the git repo (source of truth) and a Gale profile.

.DESCRIPTION
The repo's config\ is authoritative. The Gale profile and the dedicated host
are downstream copies that get overwritten.

  -Status   show what differs, change nothing (default)
  -Push     repo config\  ->  profile BepInEx\config\   (then run the validator)
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
every client must have on disk. Mod versions are not handled here: those come
from a fresh Gale profile export.

.PARAMETER ProfilePath
Gale profile root. Defaults to the OSRSheim profile under %APPDATA%, so it
resolves correctly on either machine without editing this script.
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Push')][switch]$Push,
    [Parameter(ParameterSetName = 'Pull')][switch]$Pull,
    [Parameter(ParameterSetName = 'Status')][switch]$Status,
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
        Write-Host "repo -> profile" -ForegroundColor Cyan
        Write-Host "  $RepoConfig"
        Write-Host "  $ProfConfig"
        Invoke-Sync -Source $RepoConfig -Dest $ProfConfig | Write-Host

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
