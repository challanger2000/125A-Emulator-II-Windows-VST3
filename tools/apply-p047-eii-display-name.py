#!/usr/bin/env python3
"""P047: identity-only factory class name for the E-MU Emulator II VST3.

Change only the *display name* returned by IPluginFactory(2), not the
processor UID, VST3 state codec, DSP, vendor/author attribution or firmware.
Package name is E-MU Emulator II.vst3 (both the directory and PE filename).
"""
import argparse
import subprocess
from pathlib import Path

PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
SOURCE=UP/"src/vst3/eii_vst3.cpp"

OLD='std::strncpy(info->name,"Emulator II Custom",'
NEW='std::strncpy(info->name,"E-MU Emulator II",'

def patch(s):
    if s.count(OLD)!=2:
        raise RuntimeError(f"P047 factory class name anchor: {s.count(OLD)} instead of 2")
    if "eii::vst::processorUid" not in s:
        raise RuntimeError("P047 original VST3 class CID missing")
    if 'std::strncpy(info->vendor,"Tamas (private)"' not in s:
        raise RuntimeError("P047 upstream vendor attribution unexpectedly changed")
    return s.replace(OLD,NEW)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    args=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P047 upstream changed; stop instead of guessing")
    original=SOURCE.read_text(encoding="utf-8")
    changed=patch(original)
    if args.verify:
        print("P047 factory class identity preflight: PASS")
    else:
        SOURCE.write_text(changed,encoding="utf-8",newline="\n")
        print("P047 VST3 processor and class identity: E-MU Emulator II (same UID and vendor)")
if __name__=="__main__": main()
