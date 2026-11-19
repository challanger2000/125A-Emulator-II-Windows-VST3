@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "RESULT=%~dp0P040-TEST-ERGEBNIS.txt"
> "%RESULT%" echo P040 genuine original OS3.1 Windows VST3 COM test, private media owner-local
>> "%RESULT%" echo Local date/time: %DATE% %TIME%
>> "%RESULT%" echo Test modes: 44100+48000 Hz, 1000 Hz, changed 500 Hz, silence, disconnected input
if not exist "%~dp0Test-Private-Original-EII-P040-Windows.ps1" (
  >> "%RESULT%" echo FAIL: P040 PowerShell test runner missing
  type "%RESULT%"
  if /I not "%P040_CI%"=="1" pause
  exit /b 1
)
rem Pass paths through environment variables instead of CMD quote parsing.
rem Start-Transcript in the PowerShell script mirrors actual console output to the log.
set "P040_PS1=%~dp0Test-Private-Original-EII-P040-Windows.ps1"
set "P040_ROM=%~dp0Original-ROM"
set "P040_OS=%~dp0Original-Medien\Emulator-II-OS31.emuiifd"
set "P040_CHOIR=%~dp0Original-Medien\EII-Choir.emuiifd"
echo.
echo P040: Original-Firmware-Test startet. Fortschritt erscheint hier live.
echo P040: Ergebnisse stehen parallel in "%RESULT%"
echo P040: Mehrere frische Emulator-Starts sind normal. Kein stummes schwarzes Fenster.
echo.
set "P040_LOG=%RESULT%"
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%P040_PS1%" -RomDir "%P040_ROM%" -Os31Floppy "%P040_OS%" -ChoirFloppy "%P040_CHOIR%"
set "CODE=%ERRORLEVEL%"
>> "%RESULT%" echo P040 BAT exit_code=%CODE%
echo.
if "%CODE%"=="0" (
  echo P040: PASS. Original Windows VST3 test abgeschlossen.
) else (
  echo P040: FAIL oder BLOCKED. Bitte P040-TEST-ERGEBNIS.txt in ChatGPT hochladen.
)
echo.
if /I not "%P040_CI%"=="1" pause
exit /b %CODE%
