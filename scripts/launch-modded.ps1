# Launch Valheim with the OSRSheim BepInEx profile, no Gale needed.
# -console enables the in-game console (F5) for dropthat:reload / spawn testing.
& "C:\Program Files (x86)\Steam\steamapps\common\Valheim\valheim.exe" `
  --doorstop-enabled true `
  --doorstop-target-assembly "$env:APPDATA\com.kesomannen.gale\valheim\profiles\OSRSheim\BepInEx\core\BepInEx.Preloader.dll" `
  -console
