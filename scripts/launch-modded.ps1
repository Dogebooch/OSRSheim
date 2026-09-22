# Launch Valheim with the OSRSheim BepInEx profile, no Gale needed.
# -console enables the in-game console (F5) for dropthat:reload / spawn testing.
# Archives the previous LogOutput.log to BepInEx\Logs\ first, so each session
# leaves its own readable file. BepInEx.cfg AppendLog is true, so a launch that
# bypasses this script (Gale, Steam) still never overwrites the log.

$ProfileRoot = "$env:APPDATA\com.kesomannen.gale\valheim\profiles\OSRSheim"
$Log     = "$ProfileRoot\BepInEx\LogOutput.log"
$LogDir  = "$ProfileRoot\BepInEx\Logs"

if (Test-Path $Log) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $stamp = (Get-Item $Log).LastWriteTime.ToString('yyyyMMdd-HHmmss')
    Move-Item $Log "$LogDir\LogOutput-$stamp.log" -Force
    # Keep the last 20 sessions.
    Get-ChildItem "$LogDir\LogOutput-*.log" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -Skip 20 |
        Remove-Item -Force
}

& "C:\Program Files (x86)\Steam\steamapps\common\Valheim\valheim.exe" `
  --doorstop-enabled true `
  --doorstop-target-assembly "$ProfileRoot\BepInEx\core\BepInEx.Preloader.dll" `
  -console
