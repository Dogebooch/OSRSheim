@echo off
rem Frame-time capture for Valheim. TEST TOOL ONLY (issue #66, RESEARCH 16).
rem Not a mod: nothing is installed and the game is not touched. PresentMon
rem (Intel, open source) reads Windows' own frame timing for valheim.exe.
rem Start it with Valheim already running. F11 starts a recording, F11 again
rem stops it; each recording is its own CSV in perf\captures\. Quitting Valheim
rem ends the capture and prints the summary (scripts\perf-frames.py).
rem Optional label: perf-capture.bat server -> perf\captures\STAMP-server-N.csv.
setlocal
set "ROOT=%~dp0.."
set "PM=%ROOT%\perf\PresentMon.exe"
if not exist "%PM%" (
  echo perf\PresentMon.exe is missing. Download PresentMon-2.5.1-x64.exe from
  echo https://github.com/GameTechDev/PresentMon/releases/tag/v2.5.1
  echo sha256 9bec3083069f58f911e6a512f4806db51a27bd096103087bc1d05ef54c80a191
  echo and save it as perf\PresentMon.exe.
  pause
  exit /b 1
)
tasklist /FI "IMAGENAME eq valheim.exe" | find /I "valheim.exe" >nul || (
  echo Start Valheim first, then run this again.
  pause
  exit /b 1
)
for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmm"') do set "STAMP=%%t"
if not "%~1"=="" set "STAMP=%STAMP%-%~1"
if not exist "%ROOT%\perf\captures" mkdir "%ROOT%\perf\captures"
echo Capturing valheim.exe. F11 = start/stop a recording. Quit Valheim to finish.
echo Files: perf\captures\%STAMP%-N.csv
"%PM%" --process_name valheim.exe --hotkey F11 --terminate_on_proc_exit --stop_existing_session --output_file "%ROOT%\perf\captures\%STAMP%.csv"
python "%ROOT%\scripts\perf-frames.py" "%ROOT%\perf\captures\%STAMP%-*.csv"
pause
