# P044. Genuine owner-local OS3.1 Windows VST3 native DAC/S3528 QA.
# Media must exist *inside the same extracted package*; no search, download,
# GitHub upload, synthetic ROM or extra utilities. Windows PowerShell 5.1.
[CmdletBinding()]
param([string]$KitDir)
$ErrorActionPreference='Stop'
if([string]::IsNullOrWhiteSpace($KitDir)){
    $KitDir=[System.IO.Path]::GetDirectoryName($MyInvocation.MyCommand.Path)
}
$KitDir=[System.IO.Path]::GetFullPath($KitDir)
$log=Join-Path $KitDir 'P044-TEST-ERGEBNIS.txt'
Set-Content -LiteralPath $log -Encoding UTF8 -Value (
   'P044 Original-Firmware Windows VST3 native DAC/S3528 test '+(Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))
function Log([string]$message) {
    Write-Host $message
    Add-Content -LiteralPath $log -Value $message -Encoding UTF8
}
$exe=Join-Path $KitDir 'vst3_host_test.exe'
$bundle=Join-Path $KitDir 'EmulatorII-Custom.vst3'
$binary=Join-Path $bundle 'Contents\x86_64-win\EmulatorII-Custom.vst3'
$rom=Join-Path $KitDir 'Original-ROM'
$media=Join-Path $KitDir 'Original-Medien'
$os=Join-Path $media 'Emulator-II-OS31.emuiifd'
$choir=Join-Path $media 'EII-Choir.emuiifd'
$original=[ordered]@{
    'main.bin'=(Join-Path $rom 'main.bin')
    'scanner.bin'=(Join-Path $rom 'scanner.bin')
    'ic135.bin'=(Join-Path $rom 'ic135.bin')
    'ic137.bin'=(Join-Path $rom 'ic137.bin')
    'Emulator-II-OS31.emuiifd'=$os
    'EII-Choir.emuiifd'=$choir
}
Log 'P044 Paketpruefung: VST3, Testhost und ALLE Originalmedien im selben Ordner.'
foreach($path in @($exe,$binary)+@($original.Values | ForEach-Object { $_ })){
    if(!(Test-Path -LiteralPath $path -PathType Leaf)){
        Log ('P044 BLOCKED FEHLT IM PAKET: '+[System.IO.Path]::GetFileName($path))
        exit 3
    }
    if((Get-Item -LiteralPath $path).Length -eq 0){
        Log ('P044 BLOCKED LEERE DATEI: '+[System.IO.Path]::GetFileName($path))
        exit 3
    }
}
if((Get-Item -LiteralPath $os).Length -ne 573440 -or
   (Get-Item -LiteralPath $choir).Length -ne 573440) {
    Log 'P044 BLOCKED: originale OS3.1/Choir Diskette hat falsche Groesse.'
    exit 3
}
Log ('P044 VST3 SHA256 '+(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash)
Log ('P044 TESTHOST SHA256 '+(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash)
$hashes=@{}
foreach($name in $original.Keys){
    $digest=(Get-FileHash -LiteralPath $original[$name] -Algorithm SHA256).Hash
    $hashes[$name]=$digest
    Log ('P044 ORIGINAL SHA256 '+$name+' '+$digest)
}
$before=$env:LOCALAPPDATA
$isolation=Join-Path $env:TEMP ('125A-P044-NATIVE-OWNER-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $isolation | Out-Null
$env:LOCALAPPDATA=$isolation
$exit=1
$mediaChanged=$false
try {
    Log 'P044 START: original Windows VST3 COM mit native=1 und S3528=1.'
    Log 'P044: 5 Original-Firmware-Laeufe, je SAMPLE/FORCE/STOP, SAVE BANK und MIDI-Audio.'
    # P041 Start-Transcript skipped native executable METRICS on WinPS 5.1.
    # Capture every stdout/stderr line explicitly while displaying it live.
    & $exe $bundle $rom $os $choir 'original-windows-native-p044-matrix' 2>&1 |
      ForEach-Object { Log ([string]$_) }
    $exit=$LASTEXITCODE
} catch {
    Log ('P044 HOST/TEST EXCEPTION: '+$_)
    $exit=1
} finally {
    $env:LOCALAPPDATA=$before
    Remove-Item -LiteralPath $isolation -Recurse -Force -ErrorAction SilentlyContinue
    foreach($name in $original.Keys){
        $after=(Get-FileHash -LiteralPath $original[$name] -Algorithm SHA256).Hash
        if($after -ne $hashes[$name]){
            Log ('P044 ORIGINALMEDIUM VERAENDERT: '+$name+' FAIL')
            $mediaChanged=$true
        }else{
            Log ('P044 ORIGINALMEDIUM UNVERAENDERT: '+$name+' PASS')
        }
    }
}
$captured=Get-Content -LiteralPath $log -Raw
$required=@(
 'P044 CHECK NATIVE_44100_HAS_1KHZ PASS',
 'P044 CHECK NATIVE_48000_HAS_1KHZ PASS',
 'P044 CHECK NATIVE_48000_HAS_500HZ PASS',
 'P044 CHECK NATIVE_SILENCE_NO_STALE_1000HZ PASS',
 'P044 CHECK NATIVE_SILENCE_NO_STALE_500HZ PASS',
 'P044 CHECK NATIVE_DISCONNECTED_NO_STALE_1000HZ PASS',
 'P044 CHECK ALL_FIVE_APPLIED_NATIVE_DSP_S3528_CAPTURE_SAVED_AUDITIONED PASS',
 'P044 ORIGINAL WINDOWS VST3 NATIVE DAC + S3528 OWNER-PRIVATE PASS failed_gates=0'
)
$all=$true
foreach($label in $required){
    if(!$captured.Contains($label)){
        Log ('P044 FEHLENDER NACHWEIS: '+$label)
        $all=$false
    }
}
if($exit -eq 0 -and !$mediaChanged -and $all){
    Log 'P044 FINAL ORIGINAL-FIRMWARE NATIVE DAC WINDOWS VST3 MATRIX: PASS'
    exit 0
}
Log ('P044 FINAL ORIGINAL-FIRMWARE NATIVE DAC WINDOWS VST3 MATRIX: FAIL exit='+$exit)
exit 1
