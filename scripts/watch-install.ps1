<#
.SYNOPSIS
Install (or remove) the OSRSheim background watcher on this PC: a logon task that runs scripts\watch.py.

.DESCRIPTION
What it is (read this to the player before installing; each PC decides for itself):
  - Records every play session from the character save (.fch) after the game closes: hours, kills,
    deaths, crafts, skill XP per hour, KG quests finished and custom values. Feeds the balance sim
    (scripts\sim-run.py validate).
  - Notes, for Claude: screenshots taken during the game (F12 / Win+Alt+PrtScn) and error types the
    game or server logs never showed before (scripts\host-data.py).
  - Checks every 30 min, with the game closed: main checkout behind origin/main, post-build-check.py
    errors, session rows not yet committed. Claude sees the result at the start of every session
    (SessionStart hook in .claude\settings.json) and offers each fix; a toast shows at game start
    when something breaks a session.
  - Never syncs configs, commits, pushes, or touches the Gale profile. On the host it writes only
    osrsheim-data/sessions/ (this PC's session rows), and only with a panel key in server.env.
  - Cost: one pythonw process (~20 MB RAM), one tasklist call every 15 s, below-normal priority.
  - Snaps and the session log live in <repo>\.cache\ (gitignored). With a panel key they are shared
    through the host; rows reach the repo when a Claude runs `session-log.py publish` in a branch.

Optional <repo>\server.env (gitignored; the player pastes the key; no script prints it):
  PTERO_URL=https://panel.ggservers.com, PTERO_SERVER=<server id>, PTERO_API_KEY=<panel key>
  (a subuser key needs file.read, file.read-content, file.create). Without it nothing reaches the host.

Requirements:
  - Windows 10/11, Valheim through Steam, the OSRSheim Gale profile at
    %APPDATA%\com.kesomannen.gale\valheim\profiles\OSRSheim.
  - Python 3.10+ on PATH (`python --version`); pythonw.exe ships next to it. No pip packages.
  - git on PATH, this repo cloned; run from the MAIN checkout on main, not a worktree.

Setup (the player's Claude does these steps):
  1. git pull                                   in the main checkout (main branch)
  2. powershell -ExecutionPolicy Bypass -File scripts\watch-install.ps1
  3. python scripts\watch.py status             expect "watcher: running"
  4. After the next play session: `python scripts\watch.py status` shows "last session: ...".
     To commit rows: in a branch, `python scripts\session-log.py publish`, commit reference\sessions\, PR.
  5. After a git pull that changes watch.py: step 2 again (the hook says when).
Not wanted on this PC: python scripts\watch.py decline (the hook stops asking).
Remove: powershell -ExecutionPolicy Bypass -File scripts\watch-install.ps1 -Uninstall
Logs: <repo>\.cache\watch\watch.log. Status: <repo>\.cache\watch\status.json.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File scripts\watch-install.ps1
#>
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'
$TaskName = 'OSRSheim watcher'
$Repo = (Resolve-Path "$PSScriptRoot\..").Path

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "removed task '$TaskName'"
}
if ($Uninstall) { return }

$gitDir = (git -C $Repo rev-parse --absolute-git-dir).Trim()
$common = (git -C $Repo rev-parse --path-format=absolute --git-common-dir).Trim()
if ((Resolve-Path $gitDir).Path -ne (Resolve-Path $common).Path) {
    throw "run this from the main checkout ($(Split-Path $common)), not a worktree"
}
$py = (python -c "import sys; print(sys.executable)").Trim()
$pyw = Join-Path (Split-Path $py) 'pythonw.exe'
if (-not (Test-Path $pyw)) { throw "pythonw.exe not found next to $py" }

$action = New-ScheduledTaskAction -Execute $pyw -Argument "`"$Repo\scripts\watch.py`" run" -WorkingDirectory $Repo
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew -Priority 7
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Description "OSRSheim: records play sessions, status for Claude ($Repo\scripts\watch.py)" | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "installed '$TaskName': $pyw $Repo\scripts\watch.py run (at logon, started now)"
Start-Sleep -Seconds 5
python "$Repo\scripts\watch.py" status
