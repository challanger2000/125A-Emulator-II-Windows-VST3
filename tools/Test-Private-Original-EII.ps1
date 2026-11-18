# P030 - owner-local original E-MU ROM/Choir positive Windows VST3 acceptance.
# IMPORTANT: do not commit/upload/include any ROM, OS image or original samples.
# QA-only helper; NOT needed by the final single-VST3 product.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$RomDir,
 [Parameter(Mandatory=$true)][string]$Floppy,
 [string]$KitDir=$PSScriptRoot
)
$ErrorActionPreference='Stop'
$exe=Join-Path $KitDir 'vst3_host_test.exe'
$plugin=Join-Path $KitDir 'EmulatorII-Custom.vst3'
if(-not (Test-Path -LiteralPath $exe -PathType Leaf)){throw "P030 host probe missing: $exe"}
if(-not (Test-Path -LiteralPath $plugin -PathType Container)){throw "P030 Windows VST3 bundle missing: $plugin"}
if(-not (Test-Path -LiteralPath $RomDir -PathType Container)){throw "P030 private ROM directory missing"}
if(-not (Test-Path -LiteralPath $Floppy -PathType Leaf)){throw "P030 original floppy missing"}
# Prevent a user's existing Custom VST3 default from contaminating this
# original EII comparison, and don't modify the owner's saved defaults.
$previousLocal=$env:LOCALAPPDATA
$isolated=Join-Path $env:TEMP ("125A-EII-P030-"+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $isolated | Out-Null
$env:LOCALAPPDATA=$isolated
try {
 Write-Host 'P030: checking true Windows VST3 factory, original ROM, firmware Pxx, guest MIDI, nonzero PCM, and fresh project recall...'
 & $exe $plugin $RomDir $Floppy "unused" "original-windows-audio"
 $code=$LASTEXITCODE
 if($code -ne 0){throw "P030 original-ROM Windows VST3 acceptance FAIL (exit $code)"}
 Write-Host 'P030 original-ROM Windows VST3 + original EII SSM2045 + project recall: PASS'
}finally{
 $env:LOCALAPPDATA=$previousLocal
 Remove-Item -LiteralPath $isolated -Recurse -Force -ErrorAction SilentlyContinue
}
