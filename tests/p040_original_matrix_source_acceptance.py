#!/usr/bin/env python3
"""P040 public CI source contract; never masquerades as original-ROM execution."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
h=(ROOT/"tests/p040_windows_original_adversarial.h").read_text(encoding="utf-8")
patch=(ROOT/"tools/apply-p040-original-windows-matrix.py").read_text(encoding="utf-8")
runner=(ROOT/"tools/Test-Private-Original-EII-P040-Windows.ps1").read_text(encoding="utf-8")
batch=(ROOT/"tools/START-P040-TEST.bat").read_text(encoding="utf-8")
workflow=(ROOT/".github/workflows/wav-bridge-qa.yml").read_text(encoding="utf-8")
checks={
    "actual Windows VST3 component and process input":
        'Instance in;' in h and 'in.process()' in h and
        'in.data.inputs[0].silenceFlags=0' in h,
    "test original scanner firmware controls":
        'eii::ScannerButton::Sample' in h and
        'eii::ScannerButton::Digit9' in h and
        'eii::ScannerButton::Digit0' in h,
    "capture SAR count / unknown bytes / host input counters":
        'samplereads' in h and 'sampleunknown' in h and
        'inputmissing' in h and 'inputdrops' in h and
        'capture.advance' in h,
    "original DISK7 bank save and IBStream snapshot":
        'qaSaveCurrentBank' in h and
        'decodeProject(project).hasBank()' in h,
    "44.1/48 kHz 1000 Hz independent fresh instances":
        '{"POSITIVE_44100_1000HZ",44100,1000,false}' in h and
        '{"POSITIVE_48000_1000HZ",48000,1000,false}' in h,
    "independent changed frequency 500 Hz":
        '{"NEGATIVE_CHANGED_48000_500HZ",48000,500,false}' in h and
        'amp500>0.003' in h,
    "connected-zero versus missing-input separate controls":
        '{"NEGATIVE_SILENCE_48000",48000,0,false}' in h and
        '{"NEGATIVE_DISCONNECTED_INPUT",48000,0,true}' in h and
        'in.data.numInputs=0' in h,
    "silence causally compared against 1000 and 500 Hz":
        'MUTED_GUEST_HAS_NO_STALE_1000HZ' in h and
        'MUTED_GUEST_HAS_NO_STALE_500HZ' in h and
        'DISCONNECTED_GUEST_HAS_NO_STALE_1000HZ' in h,
    "never boot fictitious original media":
        'PRIVATE ORIGINAL MEDIA ABSENT/BLOCKED' in h and
        'fs::is_regular_file' in h and 'return 3;' in h,
    "private test source patched after P038":
        '#include "p038_windows_original_host_capture.h"' in patch and
        'original-windows-p040-matrix' in patch and
        'p040WindowsOriginalAdversarial' in patch,
    "one-click, no additional runtime installation":
        'powershell.exe' in batch and
        'P040-TEST-ERGEBNIS.txt' in batch and
        'Test-Private-Original-EII-P040-Windows.ps1' in batch,
    "owner private ROM/media hashed and checked unchanged":
        'PRIVATE_MEDIA_SHA256' in runner and
        'PRIVATE MEDIA UNMODIFIED' in runner and
        'Get-FileHash' in runner,
    "public CI never imports private ROMs":
        'if ($LASTEXITCODE -ne 3)' in workflow and
        'original-windows-p040-matrix' in workflow and
        'NO-MEDIA' in workflow,
}
for name,ok in checks.items():
    print(("PASS" if ok else "FAIL")+" P040 "+name)
if not all(checks.values()):
    sys.exit(1)
print("P040 source-only contract PASS; NOT a real original-ROM Windows acceptance")
