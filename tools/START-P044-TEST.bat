@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
echo.
echo ================================================================
echo 125A EMULATOR II P044 - ORIGINAL-FIRMWARE NATIVE-DAC-TEST
echo ================================================================
echo.
echo VST3 und alle Originalmedien muessen im selben entpackten Ordner sein.
echo Testet das VST3 mit nativer DAC/Deglitch-Kette und S3528.
echo Originale ROMs/Disketten werden NICHT veraendert.
echo Fortschritt wird in diesem Fenster angezeigt.
echo Testprotokoll: P044-TEST-ERGEBNIS.txt
echo.
if not exist "%~dp0Test-Private-Original-EII-P044-Windows.ps1" (
  echo FEHLER: P044 PowerShell-Test fehlt.
  if /I not "%P044_CI%"=="1" pause
  exit /b 2
)
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0Test-Private-Original-EII-P044-Windows.ps1"
set "CODE=%ERRORLEVEL%"
echo.
if "%CODE%"=="0" (
  echo P044: ALLE ORIGINAL-FIRMWARE NATIVE-DAC-TESTS BESTANDEN.
) else (
  echo P044: TEST FEHLGESCHLAGEN ODER ORIGINALMEDIEN FEHLEN.
  echo Details: P044-TEST-ERGEBNIS.txt
)
echo.
if /I not "%P044_CI%"=="1" pause
exit /b %CODE%
