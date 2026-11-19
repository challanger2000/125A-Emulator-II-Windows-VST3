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
  pause
  exit /b 1
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Test-Private-Original-EII-P040-Windows.ps1" -KitDir "%~dp0" -RomDir "%~dp0Original-ROM" -Os31Floppy "%~dp0Original-Medien\Emulator-II-OS31.emuiifd" -ChoirFloppy "%~dp0Original-Medien\EII-Choir.emuiifd" >> "%RESULT%" 2>&1
set "CODE=%ERRORLEVEL%"
>> "%RESULT%" echo P040 BAT exit_code=%CODE%
echo.
type "%RESULT%"
echo.
if "%CODE%"=="0" (
  echo P040: PASS. Original Windows VST3 test abgeschlossen.
) else (
  echo P040: FAIL oder BLOCKED. Bitte P040-TEST-ERGEBNIS.txt in ChatGPT hochladen.
)
echo.
pause
exit /b %CODE%
