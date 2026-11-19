@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
echo.
echo ==============================================================
echo 125A Emulator II P041 - Original-Firmware Windows VST3 Test
echo ==============================================================
echo Der Test zeigt seinen Fortschritt im Fenster.
echo Ergebnisdatei: P041-TEST-ERGEBNIS.txt
echo.
if not exist "%~dp0P041-AutoLauncher.ps1" (
  echo FEHLER: P041-AutoLauncher.ps1 fehlt im Testpaket.
  if /I not "%P041_CI%"=="1" pause
  exit /b 2
)
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0P041-AutoLauncher.ps1"
set "CODE=%ERRORLEVEL%"
echo.
if "%CODE%"=="0" (
  echo P041: ALLE ORIGINAL-FIRMWARE-TESTS BESTANDEN.
) else (
  echo P041: TEST NICHT BESTANDEN ODER NICHT MOEGLICH.
  echo Siehe P041-TEST-ERGEBNIS.txt im gleichen Ordner.
)
echo.
if /I not "%P041_CI%"=="1" pause
exit /b %CODE%
