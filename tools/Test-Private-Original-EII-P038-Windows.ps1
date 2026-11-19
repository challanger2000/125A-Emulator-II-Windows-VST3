# P038 PRIVATE OWNER-LOCAL ORIGINAL OS3.1 -> HOST AUDIO IN -> SAR -> DISK7 -> PROJECT RECALL
# QA ONLY. Never commit, upload or embed original ROMs/OS images.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$RomDir,
 [Parameter(Mandatory=$true)][string]$Os31Floppy,
 [string]$KitDir=$PSScriptRoot
)
$ErrorActionPreference="Stop"
$exe=Join-Path $KitDir 'vst3_host_test.exe'
$plugin=Join-Path $KitDir 'EmulatorII-Custom.vst3'
if(-not (Test-Path -LiteralPath $exe -PathType Leaf)){throw "P038 missing actual Windows VST3 COM host test executable"}
if(-not (Test-Path -LiteralPath $plugin -PathType Container)){throw "P038 missing Windows VST3 bundle"}
foreach($name in @('main.bin','scanner.bin','ic135.bin','ic137.bin')){
 if(-not (Test-Path -LiteralPath (Join-Path $RomDir $name) -PathType Leaf)){throw "P038 missing owner original ROM $name"}
}
if(-not (Test-Path -LiteralPath $Os31Floppy -PathType Leaf)){throw "P038 missing owner original OS3.1 floppy"}
# Isolate per-user plug-in defaults and avoid touching owner's production settings.
$previous=$env:LOCALAPPDATA
$isolated=Join-Path $env:TEMP ("125A-EII-P038-"+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $isolated -Force | Out-Null
$env:LOCALAPPDATA=$isolated
try {
 Write-Host "P038 owner-only real Windows VST3 factory: original OS3.1 SAMPLE/host input/SAR/DISK7/PCM/fresh-IBStream..."
 & $exe $plugin $RomDir $Os31Floppy 'unused' 'original-windows-live-record'
 if($LASTEXITCODE -ne 0){throw "P038 actual original ROM Windows VST3 host input positive FAIL (exit $LASTEXITCODE)"}
 Write-Host 'P038 actual Windows VST3 original-firmware host input and project recall: PASS'
}finally{
 $env:LOCALAPPDATA=$previous
 Remove-Item -LiteralPath $isolated -Recurse -Force -ErrorAction SilentlyContinue
}
