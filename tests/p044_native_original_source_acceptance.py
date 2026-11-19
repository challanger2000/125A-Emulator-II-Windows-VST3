#!/usr/bin/env python3
"""P044 preflight only: source contract for real owner-only native path.
DOES NOT pretend to run licensed ROM/OS or playback in public CI.
"""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
p040=(root/"tests/p040_windows_original_adversarial.h").read_text(encoding="utf-8")
p044=(root/"tests/p044_windows_native_original_adversarial.h").read_text(encoding="utf-8")
patch=(root/"tools/apply-p044-native-original-windows-matrix.py").read_text(encoding="utf-8")
runner=(root/"tools/Test-Private-Original-EII-P044-Windows.ps1").read_text(encoding="utf-8")
bat=(root/"tools/START-P044-TEST.bat").read_text(encoding="utf-8")
workflow=(root/".github/workflows/wav-bridge-qa.yml").read_text(encoding="utf-8")
checks={
 "P041 unchanged reference mode when native flag omitted":
     'bool native=false;' in p040 and
     'state=replaceKey(state,"native",tc.native?"1":"0");' in p040,
 "native true actually applied and S3528 on":
     'in.status("appliednative")=="1"' in p040 and
     'in.status("applieds3528")=="1"' in p040,
 "requires original ROM and two original OS/image floppies":
     "P044 BLOCKED ORIGINAL MEDIA MISSING" in p044 and
     'fs::file_size(os31)!=573440' in p044 and
     'fs::file_size(choir)!=573440' in p044,
 "source uses original P040 genuine SAR/DISK7 and host audition":
     'p040OwnerCase(' in p044 and
     'qaSaveCurrentBank' in p040 and
     'EventList noteOn,noteOff;' in p040,
 "native 44.1kHz 1000Hz positive":
     '{"NATIVE_POSITIVE_44100_1000HZ",44100,1000,false,true}' in p044,
 "native 48kHz 1000Hz positive":
     '{"NATIVE_POSITIVE_48000_1000HZ",48000,1000,false,true}' in p044,
 "native 48kHz changed 500Hz positive":
     '{"NATIVE_CHANGED_48000_500HZ",48000,500,false,true}' in p044,
 "native zero input and real removed VST3 input bus":
     '{"NATIVE_SILENCE_48000",48000,0,false,true}' in p044 and
     '{"NATIVE_DISCONNECTED_48000",48000,0,true,true}' in p044 and
     'in.data.numInputs=0' in p040,
 "fail closed if any of seven native checks absent":
     'ALL_FIVE_APPLIED_NATIVE_DSP_S3528_CAPTURE_SAVED_AUDITIONED' in p044 and
     'failed_gates=' in p044,
 "no private media or false positive from public CI":
     'return 3;' in p044 and 'NO FAKE NATIVE-AUDIO PASS' in p044 and
     '"original-windows-native-p044-matrix"' in workflow,
 "one-click private package and full stdout logging":
     'powershell.exe' in bat and 'P044-TEST-ERGEBNIS.txt' in bat and
     "ForEach-Object { Log ([string]$_) }" in runner,
 "independent owner-original SHA-256 unchanged checks":
     'Get-FileHash' in runner and 'ORIGINALMEDIUM UNVERAENDERT' in runner and
     'Original-ROM' in runner and 'Original-Medien' in runner,
 "old P041/040 mode still dispatched separately":
     'original-windows-p040-matrix' in patch and
     'original-windows-native-p044-matrix' in patch
}
bad=[n for n,ok in checks.items() if not ok]
for name,ok in checks.items():
    print(("PASS " if ok else "FAIL ")+name)
if bad:
    raise SystemExit(f"P044 SOURCE-ONLY CONTRACT FAIL: {len(bad)}")
print("P044 SOURCE CONTRACT PASS; ORIGINAL FIRMWARE WINDOWS AUDIO NOT EXECUTED")
