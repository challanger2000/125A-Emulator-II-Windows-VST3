# 125A P006: LOCAL PRIVATE package only, same structure as Vintage Sampler III.
# Never commit, upload, or distribute this package with original E-mu ROMs/OS.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$BuiltPluginFolder,
 [Parameter(Mandatory=$true)][string]$RomDir,
 [Parameter(Mandatory=$true)][string]$OsImage,
 [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference='Stop'
$plugin=Join-Path $BuiltPluginFolder 'EmulatorII-Custom.vst3/Contents/x86_64-win/EmulatorII-Custom.vst3'
if(-not (Test-Path -LiteralPath $plugin -PathType Leaf)){throw "Missing built VST3: $plugin"}
if(-not (Test-Path -LiteralPath $OsImage -PathType Leaf)){throw "Missing original OS image: $OsImage"}
$ext=[IO.Path]::GetExtension($OsImage).ToLowerInvariant()
if($ext -notin @('.hfe','.emuiifd')){throw 'Original EII OS must be HFE or EMUIIFD'}
if($ext -eq '.emuiifd' -and (Get-Item -LiteralPath $OsImage).Length -ne 573440){
 throw 'EMUIIFD original OS image must be 573440 bytes'
}
$roms=@{'main.bin'=8192;'scanner.bin'=8192;'ic135.bin'=512;'ic137.bin'=512}
$optional=@{'main21dm.bin'=8192;'main23.bin'=8192;'scanner21.bin'=8192}
foreach($entry in $roms.GetEnumerator()){
 $p=Join-Path $RomDir $entry.Key
 if(-not (Test-Path -LiteralPath $p -PathType Leaf) -or (Get-Item -LiteralPath $p).Length -ne $entry.Value){
  throw "Missing or wrong-size Emulator II ROM: $p"
 }
}
foreach($entry in $optional.GetEnumerator()){
 $p=Join-Path $RomDir $entry.Key
 if((Test-Path -LiteralPath $p -PathType Leaf) -and (Get-Item -LiteralPath $p).Length -ne $entry.Value){
  throw "Wrong-size optional EII ROM: $p"
 }
}
$target=Join-Path $Destination 'E-MU Emulator II.vst3'
if(Test-Path -LiteralPath $target){throw "Existing VST3 will not be overwritten: $target"}
$created=$false
try{
 $bin=Join-Path $target 'Contents/x86_64-win'
 $rom=Join-Path $target 'Contents/Resources/ROM'
 $os=Join-Path $target 'Contents/Resources/OS'
 foreach($folder in @($bin,$rom,$os)){New-Item -ItemType Directory -Force -Path $folder | Out-Null}
 $created=$true
 Copy-Item -LiteralPath $plugin -Destination (Join-Path $bin 'E-MU Emulator II.vst3')
 foreach($name in $roms.Keys){Copy-Item -LiteralPath (Join-Path $RomDir $name) -Destination (Join-Path $rom $name)}
 foreach($name in $optional.Keys){
  $p=Join-Path $RomDir $name
  if(Test-Path -LiteralPath $p -PathType Leaf){Copy-Item -LiteralPath $p -Destination (Join-Path $rom $name)}
 }
 Copy-Item -LiteralPath $OsImage -Destination (Join-Path $os ([IO.Path]::GetFileName($OsImage)))
 Write-Host "Private Emulator II VST3 ready: $target"
 Write-Host 'Copy the whole .vst3 folder to Common Files\VST3\Eigene while Studio One is closed.'
 Write-Host 'Do not distribute this owner-only package containing original E-mu firmware.'
}catch{
 if($created -and (Test-Path -LiteralPath $target)){Remove-Item -LiteralPath $target -Recurse -Force}
 throw
}
