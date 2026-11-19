# P041 owner-only original OS 3.1 Windows VST3 test launcher.
# No private ROM/OS/sample contents are copied to the new kit or uploaded.
# PowerShell 5.1 compatible. Launch from START-P041-TEST.bat.
[CmdletBinding()]
param([string]$MediaRoot)
$ErrorActionPreference='Stop'
$kit=[System.IO.Path]::GetDirectoryName($MyInvocation.MyCommand.Path)
$log=Join-Path $kit 'P041-TEST-ERGEBNIS.txt'
$header="P041 local original-firmware Windows VST3 diagnostic; "+(Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
Set-Content -LiteralPath $log -Value $header -Encoding UTF8
function Report([string]$message) {
    Write-Host $message
    Add-Content -LiteralPath $log -Value $message -Encoding UTF8
}
if (-not (Test-Path -LiteralPath (Join-Path $kit 'vst3_host_test.exe') -PathType Leaf)) {
    Report 'BLOCKED: komplettes Testpaket fehlt (vst3_host_test.exe).'
    exit 2
}
if (-not (Test-Path -LiteralPath (Join-Path $kit 'EmulatorII-Custom.vst3\Contents\x86_64-win\EmulatorII-Custom.vst3') -PathType Leaf)) {
    Report 'BLOCKED: VST3 ist nicht im Testpaket enthalten.'
    exit 2
}
if (-not (Test-Path -LiteralPath (Join-Path $kit 'Test-Private-Original-EII-P040-Windows.ps1') -PathType Leaf)) {
    Report 'BLOCKED: Original-Firmware-Testskript fehlt.'
    exit 2
}
$candidates=New-Object 'System.Collections.Generic.List[string]'
if (-not [string]::IsNullOrWhiteSpace($MediaRoot)) { $candidates.Add($MediaRoot) }
$candidates.Add($kit)
$parent=[System.IO.Directory]::GetParent($kit)
if ($null -ne $parent) {
    $candidates.Add((Join-Path $parent.FullName '125A-Emulator-II-P040-Test'))
}
$homeDir=[Environment]::GetFolderPath('UserProfile')
if (-not [string]::IsNullOrWhiteSpace($homeDir)) {
    $candidates.Add((Join-Path $homeDir 'Downloads\125A-Emulator-II-P040-Test'))
}
$media=$null
foreach ($root in $candidates) {
    $rom=Join-Path $root 'Original-ROM'
    $images=Join-Path $root 'Original-Medien'
    $required=@(
        (Join-Path $rom 'main.bin'),
        (Join-Path $rom 'scanner.bin'),
        (Join-Path $rom 'ic135.bin'),
        (Join-Path $rom 'ic137.bin'),
        (Join-Path $images 'Emulator-II-OS31.emuiifd'),
        (Join-Path $images 'EII-Choir.emuiifd')
    )
    $complete=$true
    foreach($file in $required) {
        if(-not (Test-Path -LiteralPath $file -PathType Leaf)) {$complete=$false;break}
    }
    if($complete) {
        $media=[pscustomobject]@{
            Root=$root; Rom=$rom;
            OS=(Join-Path $images 'Emulator-II-OS31.emuiifd');
            Choir=(Join-Path $images 'EII-Choir.emuiifd')
        }
        break
    }
}
if ($null -eq $media) {
    Report 'BLOCKED: Originalmedien nicht gefunden.'
    Report 'Gesucht wurde im neuen Ordner und im bisherigen Downloads\125A-Emulator-II-P040-Test.'
    Report 'Die Originalmedien muessen lokal bleiben; nicht in GitHub hochladen.'
    exit 3
}
Report 'P041: Originalmedien im bisherigen lokalen Ordner gefunden.'
Report 'P041: Reale Windows-VST3-Tests mit neuer Original-Firmware-Speicherdiagnose starten.'
Report 'P041: Der Test zeigt die einzelnen Faelle und Save-Phasen direkt im Fenster.'
$env:P040_LOG=$log
$script=Join-Path $kit 'Test-Private-Original-EII-P040-Windows.ps1'
& $script -RomDir $media.Rom -Os31Floppy $media.OS -ChoirFloppy $media.Choir
$code=$LASTEXITCODE
if ($null -eq $code) { $code=1 }
if ($code -eq 0) {
    Report 'P041 FINAL WINDOWS ORIGINAL FIRMWARE MATRIX: PASS'
} else {
    Report ("P041 FINAL WINDOWS ORIGINAL FIRMWARE MATRIX: FAIL OR BLOCKED exit="+$code)
}
exit $code
