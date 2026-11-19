# Owner-local only. Genuine Emulator II ROMs/OS3.1/Choir stay on this computer.
# P040 original Windows VST3 COM adversarial acceptance. No Studio One needed.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$RomDir,
 [Parameter(Mandatory=$true)][string]$Os31Floppy,
 [Parameter(Mandatory=$true)][string]$ChoirFloppy,
 [string]$KitDir
)
$ErrorActionPreference='Stop'
# On Windows PowerShell 5.1, $PSScriptRoot in a parameter default can be
# empty before the invocation scope is fully established. Compute from the
# absolute script filename at runtime instead of using that fragile default.
if ([string]::IsNullOrWhiteSpace($KitDir)) {
 $KitDir=[System.IO.Path]::GetDirectoryName($MyInvocation.MyCommand.Path)
}
if ([string]::IsNullOrWhiteSpace($KitDir)) {
 throw 'P040 test folder could not be resolved from script path'
}
$KitDir=[System.IO.Path]::GetFullPath($KitDir)
# Owner one-click BAT sets P040_LOG. PowerShell's transcript records the same
# real-time host output that appears on screen, including Write-Host and stderr.
# The standalone no-media smoke intentionally runs without a transcript.
if (-not [string]::IsNullOrWhiteSpace($env:P040_LOG)) {
    Start-Transcript -LiteralPath $env:P040_LOG -Append | Out-Null
}
Write-Host ('P040 SCRIPT_DIR '+$KitDir)
$exe=Join-Path $KitDir 'vst3_host_test.exe'
$bundle=Join-Path $KitDir 'EmulatorII-Custom.vst3'
$binary=Join-Path $bundle 'Contents\x86_64-win\EmulatorII-Custom.vst3'
$private=[ordered]@{
 'main.bin'=(Join-Path $RomDir 'main.bin')
 'scanner.bin'=(Join-Path $RomDir 'scanner.bin')
 'ic135.bin'=(Join-Path $RomDir 'ic135.bin')
 'ic137.bin'=(Join-Path $RomDir 'ic137.bin')
 'OS31.emuiifd'=$Os31Floppy
 'Choir.emuiifd'=$ChoirFloppy
}
if(!(Test-Path -LiteralPath $exe -PathType Leaf)){throw 'P040 actual Windows VST3 COM test executable missing'}
if(!(Test-Path -LiteralPath $binary -PathType Leaf)){throw 'P040 actual Windows VST3 binary missing'}
$before=@{}
Write-Host 'P040 ORIGINAL WINDOWS VST3: ROM/OS3.1/CHOIR + 44.1/48kHz + 1k/500Hz + SILENCE + NO INPUT'
Write-Host 'P040 SOURCE Windows COM original firmware matrix; no synthetic firmware and no direct RAM injection'
Write-Host ('P040 VST3 SHA256 '+(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash)
foreach($name in $private.Keys) {
 $path=[string]$private[$name]
 if(!(Test-Path -LiteralPath $path -PathType Leaf)){throw ('P040 missing owner-original media: '+$name)}
 $digest=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
 $before[$name]=$digest
 Write-Host ('P040 PRIVATE_MEDIA_SHA256 '+$name+' '+$digest)
}
$originalLocalAppData=$env:LOCALAPPDATA
$isolated=Join-Path $env:TEMP ('125A-P040-TEST-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $isolated -Force|Out-Null
$env:LOCALAPPDATA=$isolated
$failed=$false
try {
 & $exe $bundle $RomDir $Os31Floppy $ChoirFloppy 'original-windows-p040-matrix'
 $code=$LASTEXITCODE
 if($code -ne 0){throw ('P040 original Windows VST3 adversarial matrix failed; exit code '+$code)}
 Write-Host 'P040 WINDOWS VST3 ORIGINAL FIRMWARE MULTIRATE/CAUSAL NEGATIVE: PASS'
}catch{
 Write-Host ('P040 TEST FAILED: '+$_)
 $failed=$true
}finally{
 $env:LOCALAPPDATA=$originalLocalAppData
 Remove-Item -LiteralPath $isolated -Force -Recurse -ErrorAction SilentlyContinue
 foreach($name in $private.Keys){
  $after=(Get-FileHash -LiteralPath ([string]$private[$name]) -Algorithm SHA256).Hash
  if($after -ne $before[$name]){
    Write-Host ('P040 PRIVATE MEDIA CHANGED: '+$name+' FAIL')
    $failed=$true
  }else{
    Write-Host ('P040 PRIVATE MEDIA UNMODIFIED: '+$name+' PASS')
  }
 }
}
if($failed){
    if ($env:P040_LOG) { Stop-Transcript | Out-Null }
    exit 1
}
Write-Host 'P040 FINAL ORIGINAL-FIRMWARE WINDOWS VST3 TEST: PASS'
if ($env:P040_LOG) { Stop-Transcript | Out-Null }
exit 0
