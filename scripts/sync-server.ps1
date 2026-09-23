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
  permissions.yaml alias.yaml binds.yaml server_devcommands.cfg   devcommands
Overwriting any of these with a copy from a test world loses server progress.

Client-only files are listed, never uploaded; the server never reads them:
  Marketplace_SavedNPCs\        KG Hammer templates (MarketplaceHammer is a Client module)

Host-only values live in $HostOverrides. They are written into a staged copy
of the repo file just before comparing and uploading; the repo and the Gale
profile keep their own values. Drop That and Spawn That debug dumps are off on
the host: they load every location prefab at boot (RESEARCH.md, Server setup).

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
$LiveDirs  = @('Marketplace\SavedData', 'EpicLoot\BountySaves', 'KeyManager')
$LiveFiles = @('permissions.yaml', 'alias.yaml', 'binds.yaml', 'server_devcommands.cfg')
# Client-only: the server never reads these. Listed, never uploaded.
$ClientDirs = @('Marketplace_SavedNPCs')
# Host-only config values. File is relative to config\; Section and Key take wildcards.
# Every rule must match at least one key, or the run stops before touching the host.
$HostOverrides = @(
    # Debug dumps load every location prefab at boot: 10.6 GiB peak with MWL, 2.5 GiB without them.
    @{ File = 'drop_that.cfg';  Section = '*'; Key = 'Write*'; Value = 'false' },
    @{ File = 'spawn_that.cfg'; Section = '*'; Key = 'Write*'; Value = 'false' },
    # Clients run without the BepInEx console (frame stalls); the panel console needs it.
    @{ File = 'BepInEx.cfg'; Section = 'Logging.Console'; Key = 'Enabled'; Value = 'true' }
)
$Stage  = Join-Path $env:TEMP 'osrsheim-server-stage'
$Staged = @{}
$OverrideReport = @()

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
function Test-Client([string]$Rel) {
    foreach ($d in $ClientDirs) { if ($Rel -like "$d\*") { return $true } }
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
    # Windows PowerShell 5.1 turns native stderr into a terminating error under Stop;
    # OpenSSH 10 warns on stderr about the host's non-post-quantum key exchange.
    $ErrorActionPreference = 'Continue'
    $out = & sftp -o BatchMode=yes -o ConnectTimeout=20 -b $batch $SshHost 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { $out | Write-Host; throw "sftp exited $LASTEXITCODE" }
    return $out
}
function ToSftp([string]$Path) { return $Path -replace '\\', '/' }

function New-HostStage {
    # Copy each overridden repo file into $Stage and rewrite the matching keys there.
    if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
    $script:Staged = @{}
    $script:OverrideReport = @()
    $utf8 = New-Object Text.UTF8Encoding($false)
    foreach ($group in ($HostOverrides | Group-Object { $_.File })) {
        $rel = $group.Name -replace '/', '\'
        $src = Join-Path $RepoConfig $rel
        if (-not (Test-Path $src)) { throw "Host override names a missing file: config\$rel" }
        $rules = @($group.Group)
        $hits  = New-Object int[] $rules.Count
        # Split on LF only, so each line keeps its own CR: these cfgs mix CRLF and LF.
        $lines = $utf8.GetString([IO.File]::ReadAllBytes($src)) -split "`n"
        $section = ''
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match '^\s*\[(.+?)\]\s*\r?$') { $section = $Matches[1]; continue }
            if ($lines[$i] -notmatch '^(\s*)([^#;\s][^=]*?)(\s*=\s*)(.*?)(\r?)$') { continue }
            $indent = $Matches[1]; $key = $Matches[2]; $eq = $Matches[3]; $old = $Matches[4]; $cr = $Matches[5]
            for ($j = 0; $j -lt $rules.Count; $j++) {
                if ($section -like $rules[$j].Section -and $key -like $rules[$j].Key) {
                    $lines[$i] = $indent + $key + $eq + $rules[$j].Value + $cr
                    $hits[$j]++
                    if ($old -ne $rules[$j].Value) {
                        $script:OverrideReport += "  $rel [$section] $key = $($rules[$j].Value)   (repo: $old)"
                    }
                    break
                }
            }
        }
        for ($j = 0; $j -lt $rules.Count; $j++) {
            if ($hits[$j] -eq 0) { throw "Host override matched no key: $rel [$($rules[$j].Section)] $($rules[$j].Key)" }
        }
        $dest = Join-Path $Stage $rel
        New-Item -ItemType Directory -Force (Split-Path -Parent $dest) | Out-Null
        [IO.File]::WriteAllBytes($dest, $utf8.GetBytes($lines -join "`n"))
        $script:Staged[$rel] = $dest
    }
}
function Get-Source([string]$Rel) {
    # The file uploaded for $Rel: the staged copy if it carries host overrides, else the repo file.
    if ($Staged.ContainsKey($Rel)) { return $Staged[$Rel] }
    return Join-Path $RepoConfig $Rel
}

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
    foreach ($k in @($Staged.Keys)) { if ($repo.ContainsKey($k)) { $repo[$k] = Get-NormalizedHash $Staged[$k] } }
    $srv  = Get-Tree $HostConfig
    $r = [ordered]@{ same = 0; differs = @(); onlyRepo = @(); onlyHost = @(); live = @(); client = @() }
    foreach ($k in ($repo.Keys | Sort-Object)) {
        if (Test-Client $k) { $r.client += $k; continue }
        if (Test-Live $k) { $r.live += $k; continue }
        if (-not $srv.ContainsKey($k)) { $r.onlyRepo += $k }
        elseif ($srv[$k] -ne $repo[$k]) { $r.differs += $k }
        else { $r.same++ }
    }
    foreach ($k in ($srv.Keys | Sort-Object)) {
        if (-not $repo.ContainsKey($k) -and -not (Test-Live $k) -and -not (Test-Client $k)) { $r.onlyHost += $k }
    }
    return $r
}

function Show-Report($r) {
    Write-Host "`nidentical: $($r.same)   differs: $($r.differs.Count)   missing on host: $($r.onlyRepo.Count)   host extras: $($r.onlyHost.Count)"
    if ($r.differs)  { Write-Host "`nDIFFERS (repo wins on -Deploy):" -ForegroundColor Yellow; $r.differs  | ForEach-Object { "  $_" } }
    if ($r.onlyRepo) { Write-Host "`nMISSING ON HOST (uploaded on -Deploy):" -ForegroundColor Yellow; $r.onlyRepo | ForEach-Object { "  $_" } }
    if ($r.live)     { Write-Host "`nLIVE STATE, tracked in git but never uploaded:" -ForegroundColor DarkGray; $r.live | ForEach-Object { "  $_" } }
    if ($r.client)   { Write-Host "`nCLIENT ONLY, the server never reads these, never uploaded:" -ForegroundColor DarkGray; $r.client | ForEach-Object { "  $_" } }
    if ($OverrideReport) { Write-Host "`nHOST OVERRIDES, applied to the upload only:" -ForegroundColor DarkGray; $OverrideReport }
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
        New-HostStage
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
            $cmds += "put `"$(ToSftp (Get-Source $f))`" `"$RemoteConfig/$(ToSftp $f)`""
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
        New-HostStage
        Fetch-Host
        $r = Compare-Trees
        Show-Report $r
        Write-Host "`nRe-run with -Deploy (host stopped) to apply." -ForegroundColor Yellow
    }
}
exit 0
