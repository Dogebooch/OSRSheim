<#
.SYNOPSIS
Compare or deploy the repo's config\ to the dedicated host over SFTP.

.DESCRIPTION
The repo's config\ is authoritative; the host's BepInEx\config is a downstream
copy. Same idea as sync-configs.ps1, one hop further.

  -Status   download the host's config, report drift, change nothing (default)
  -Deploy   upload every repo file that differs from or is missing on the host
  -Fetch    download the host's BepInEx\config and LogOutput.log only

Never deletes. Extras on the host are listed, not removed.

Comparison ignores CRLF/LF: the host is Linux and rewrites cfg files with LF
on start, which is not drift. Mod-shipped examples and backups are skipped
as in .gitignore.

Live host state is never uploaded even though some of it is tracked in git:
  Marketplace\SavedData\        KG's live database (bank, NPC state)
  EpicLoot\BountySaves\         live bounty ledgers
  KeyManager\                   KG licence cache
  Marketplace_SavedNPCs\        placed NPCs
  permissions.yaml alias.yaml binds.yaml server_devcommands.cfg   devcommands
Overwriting any of these with a copy from a test world loses server progress.

Deploy with the host STOPPED: mods read cfg at start and some write theirs
back on shutdown, which would undo the upload.

Auth is the SSH alias in ~\.ssh\config (key only, no password anywhere):
  Host osrsheim  HostName d1228.ggn.io  Port 2022  User <panel user>.<server id>
  IdentityFile ~/.ssh/osrsheim_ggservers
The public key is registered on panel.ggservers.com -> Account -> SSH Key.

.EXAMPLE
  .\scripts\sync-server.ps1                 # what differs
  .\scripts\sync-server.ps1 -Deploy         # stop the host first
  .\scripts\sync-server.ps1 -Fetch          # then read <temp>\BepInEx\LogOutput.log

.PARAMETER SshHost
Alias from ~\.ssh\config. Default osrsheim.

.PARAMETER RemoteConfig
Path on the host, relative to the SFTP root. Default BepInEx/config.
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Deploy')][switch]$Deploy,
    [Parameter(ParameterSetName = 'Fetch')][switch]$Fetch,
    [Parameter(ParameterSetName = 'Status')][switch]$Status,
    [string]$SshHost = 'osrsheim',
    [string]$RemoteConfig = 'BepInEx/config'
)

$ErrorActionPreference = 'Stop'

$RepoRoot   = Split-Path -Parent $PSScriptRoot
$RepoConfig = Join-Path $RepoRoot 'config'
$Work       = Join-Path $env:TEMP 'osrsheim-server'
$HostConfig = Join-Path $Work 'BepInEx\config'

# Mirrors .gitignore and sync-configs.ps1. Keep the three in step.
$ExcludeFiles = @('*.bak', '*.bak-*', '*.bak.*', '*.cllc-example', '*.log', '*.log.*', '.gitkeep')
$ExcludeDirs  = @('Marketplace_CachedImages', 'Marketplace_KGChat_Emojis', 'Marketplace_Models',
                  'Marketplace_Sounds', 'Marketplace_VideoClips', 'Cache', 'wackyDatabase-BulkYML')
# Host-only live state: compared for information, never uploaded.
$LiveDirs  = @('Marketplace\SavedData', 'EpicLoot\BountySaves', 'KeyManager', 'Marketplace_SavedNPCs')
$LiveFiles = @('permissions.yaml', 'alias.yaml', 'binds.yaml', 'server_devcommands.cfg')

function Test-Excluded([string]$Rel) {
    $name = Split-Path -Leaf $Rel
    foreach ($p in $ExcludeFiles) { if ($name -like $p) { return $true } }
    foreach ($d in $ExcludeDirs)  { if ($Rel -match "(^|\\)$([regex]::Escape($d))(\\|$)") { return $true } }
    return $false
}
function Test-Live([string]$Rel) {
    if ($LiveFiles -contains $Rel) { return $true }
    foreach ($d in $LiveDirs) { if ($Rel -like "$d\*") { return $true } }
    return $false
}
function Get-NormalizedHash([string]$Path) {
    # CRLF -> LF before hashing so the Linux rewrite is not drift.
    $bytes = [IO.File]::ReadAllBytes($Path)
    $text  = [Text.Encoding]::UTF8.GetString($bytes) -replace "`r`n", "`n"
    $sha   = [Security.Cryptography.SHA1]::Create()
    return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($text)))
}
function Get-Tree([string]$Root) {
    $m = @{}
    Get-ChildItem $Root -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($Root.Length + 1)
        if (-not (Test-Excluded $rel)) { $m[$rel] = Get-NormalizedHash $_.FullName }
    }
    return $m
}
function Invoke-Sftp([string[]]$Commands) {
    $batch = Join-Path $Work 'batch.txt'
    [IO.File]::WriteAllText($batch, (($Commands + 'bye') -join "`n") + "`n", [Text.Encoding]::ASCII)
    $out = & sftp -o BatchMode=yes -o ConnectTimeout=20 -b $batch $SshHost 2>&1
    if ($LASTEXITCODE -ne 0) { $out | Write-Host; throw "sftp exited $LASTEXITCODE" }
    return $out
}
function ToSftp([string]$Path) { return $Path -replace '\\', '/' }

function Fetch-Host {
    if (Test-Path $Work) { Remove-Item $Work -Recurse -Force }
    New-Item -ItemType Directory -Force (Join-Path $Work 'BepInEx') | Out-Null
    Write-Host "host -> $Work" -ForegroundColor Cyan
    Invoke-Sftp @(
        "get -r $RemoteConfig $(ToSftp $HostConfig)",
        "-get $(Split-Path -Parent $RemoteConfig)/LogOutput.log $(ToSftp (Join-Path $Work 'BepInEx\LogOutput.log'))"
    ) | Out-Null
}

function Compare-Trees {
    $repo = Get-Tree $RepoConfig
    $srv  = Get-Tree $HostConfig
    $r = [ordered]@{ same = 0; differs = @(); onlyRepo = @(); onlyHost = @(); live = @() }
    foreach ($k in ($repo.Keys | Sort-Object)) {
        if (Test-Live $k) { $r.live += $k; continue }
        if (-not $srv.ContainsKey($k)) { $r.onlyRepo += $k }
        elseif ($srv[$k] -ne $repo[$k]) { $r.differs += $k }
        else { $r.same++ }
    }
    foreach ($k in ($srv.Keys | Sort-Object)) {
        if (-not $repo.ContainsKey($k) -and -not (Test-Live $k)) { $r.onlyHost += $k }
    }
    return $r
}

function Show-Report($r) {
    Write-Host "`nidentical: $($r.same)   differs: $($r.differs.Count)   missing on host: $($r.onlyRepo.Count)   host extras: $($r.onlyHost.Count)"
    if ($r.differs)  { Write-Host "`nDIFFERS (repo wins on -Deploy):" -ForegroundColor Yellow; $r.differs  | ForEach-Object { "  $_" } }
    if ($r.onlyRepo) { Write-Host "`nMISSING ON HOST (uploaded on -Deploy):" -ForegroundColor Yellow; $r.onlyRepo | ForEach-Object { "  $_" } }
    if ($r.live)     { Write-Host "`nLIVE STATE, tracked in git but never uploaded:" -ForegroundColor DarkGray; $r.live | ForEach-Object { "  $_" } }
    if ($r.onlyHost) {
        $top = $r.onlyHost | ForEach-Object { ($_ -split '\\')[0] } | Group-Object | Sort-Object Count -Descending
        Write-Host "`nHOST EXTRAS (never removed): $($r.onlyHost.Count) files" -ForegroundColor DarkGray
        $top | ForEach-Object { "  {0,4}  {1}" -f $_.Count, $_.Name }
    }
}

if (-not (Test-Path $RepoConfig)) { throw "Not found: $RepoConfig" }

switch ($PSCmdlet.ParameterSetName) {
    'Fetch' {
        Fetch-Host
        Write-Host "Downloaded. Log: $(Join-Path $Work 'BepInEx\LogOutput.log')" -ForegroundColor Green
    }
    'Deploy' {
        Fetch-Host
        $r = Compare-Trees
        Show-Report $r
        $files = @($r.differs) + @($r.onlyRepo)
        if (-not $files) { Write-Host "`nHost already matches the repo." -ForegroundColor Green; break }

        Write-Host "`nrepo -> host: $($files.Count) file(s)" -ForegroundColor Cyan
        $dirs = $files | ForEach-Object { Split-Path -Parent $_ } | Where-Object { $_ } | Sort-Object -Unique
        $cmds = @()
        foreach ($d in $dirs) {
            # create each level; leading '-' tells sftp to ignore "already exists"
            $acc = ''
            foreach ($part in ($d -split '\\')) {
                $acc = if ($acc) { "$acc/$part" } else { $part }
                $cmds += "-mkdir $RemoteConfig/$acc"
            }
        }
        $cmds = $cmds | Select-Object -Unique
        foreach ($f in $files) {
            $cmds += "put `"$(ToSftp (Join-Path $RepoConfig $f))`" `"$RemoteConfig/$(ToSftp $f)`""
        }
        Invoke-Sftp $cmds | Where-Object { $_ -match '^(sftp> put|Uploading)' } | ForEach-Object { "  $_" }

        Write-Host "`nverifying" -ForegroundColor Cyan
        Fetch-Host
        $after = Compare-Trees
        Show-Report $after
        if ($after.differs -or $after.onlyRepo) { Write-Host "`nDRIFT REMAINS after deploy." -ForegroundColor Red; exit 1 }
        Write-Host "`nHost config matches the repo. Start the host, then -Fetch and read the log." -ForegroundColor Green
    }
    default {
        Fetch-Host
        $r = Compare-Trees
        Show-Report $r
        Write-Host "`nRe-run with -Deploy (host stopped) to apply." -ForegroundColor Yellow
    }
}
exit 0
