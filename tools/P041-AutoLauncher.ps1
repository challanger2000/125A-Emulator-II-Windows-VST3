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
# Reuse previously working original media in place, even if the old P040
# test folder has been renamed, duplicated, or nested after ZIP extraction.
# Only scan local user-selected roots and conventional download locations.
# Never copy/read media bytes, browse entire drives, or upload anything.
$candidates=New-Object 'System.Collections.Generic.List[string]'
$seen=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
$script:visited=0
$script:maxVisited=3500
function Add-Root([string]$root) {
    if([string]::IsNullOrWhiteSpace($root)){return}
    try {
        $full=[System.IO.Path]::GetFullPath($root)
        if((Test-Path -LiteralPath $full -PathType Container) -and $seen.Add($full)) {
            $candidates.Add($full)
        }
    } catch {}
}
function Scan-Tree([string]$base,[int]$depth) {
    if([string]::IsNullOrWhiteSpace($base) -or
       -not (Test-Path -LiteralPath $base -PathType Container)){return}
    $queue=New-Object System.Collections.Queue
    $queue.Enqueue([pscustomobject]@{Path=$base;Level=0})
    while($queue.Count -gt 0 -and $script:visited -lt $script:maxVisited){
        $entry=$queue.Dequeue()
        $script:visited++
        Add-Root $entry.Path
        if($entry.Level -ge $depth){continue}
        $children=@(Get-ChildItem -LiteralPath $entry.Path -Directory -ErrorAction SilentlyContinue)
        foreach($child in $children) {
            # Avoid descending into unrelated large development/data folders.
            if($child.Name -in @('node_modules','.git','.venv','Windows',
                                'Program Files','Program Files (x86)','$Recycle.Bin')) {continue}
            $queue.Enqueue([pscustomobject]@{
                Path=$child.FullName
                Level=($entry.Level+1)
            })
        }
    }
}
Add-Root $MediaRoot
Add-Root $kit
$parent=[System.IO.Directory]::GetParent($kit)
if($null -ne $parent) {
    Add-Root (Join-Path $parent.FullName '125A-Emulator-II-P040-Test')
    # ZIP tools sometimes add an extra enclosing directory.
    Add-Root $parent.FullName
    if($null -ne $parent.Parent) {
        Add-Root (Join-Path $parent.Parent.FullName '125A-Emulator-II-P040-Test')
    }
}
$homeDir=[Environment]::GetFolderPath('UserProfile')
$downloads=$null
if(-not [string]::IsNullOrWhiteSpace($homeDir)) {
    $downloads=Join-Path $homeDir 'Downloads'
    Add-Root (Join-Path $downloads '125A-Emulator-II-P040-Test')
}
# Windows permits Explorer's Downloads folder to be redirected (e.g. OneDrive
# or another volume). Resolve the per-user Known Folder registry entry.
$redirected=$null
try {
    $key=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders' -ErrorAction Stop
    $prop=$key.PSObject.Properties['{374DE290-123F-4565-9164-39C4925E467B}']
    if($null -ne $prop -and -not [string]::IsNullOrWhiteSpace([string]$prop.Value)){
        $redirected=[Environment]::ExpandEnvironmentVariables([string]$prop.Value)
    }
} catch {}
# Fast, exact guesses first, before wider bounded directory walks.
if($redirected){Add-Root (Join-Path $redirected '125A-Emulator-II-P040-Test')}
# A renamed P040 folder, duplicate extraction, or nested test kit can be up to
# four directory levels below Downloads; no global filesystem traversal.
Write-Host 'P041: Suche lokale Originalmedien in frueheren Testordnern ...'
if($MediaRoot){Scan-Tree $MediaRoot 3}
if($null -ne $parent){Scan-Tree $parent.FullName 2}
if($downloads){Scan-Tree $downloads 4}
if($redirected -and $redirected -ne $downloads){Scan-Tree $redirected 4}
$desktop=[Environment]::GetFolderPath('Desktop')
$documents=[Environment]::GetFolderPath('MyDocuments')
if($desktop){Scan-Tree $desktop 2}
if($documents){Scan-Tree $documents 2}
Report ('P041: Untersuchte lokale Testordner: '+$candidates.Count)
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
    Report 'Geprueft: bisheriger Testordner, umbenannte/nestete Downloads, Desktop, Dokumente und umgeleitete Downloads.'
    Report 'Die Originalmedien muessen lokal bleiben; nicht in GitHub hochladen.'
    exit 3
}
Report 'P041: Vollstaendige Originalmedien in einem lokalen Testordner gefunden.'
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
