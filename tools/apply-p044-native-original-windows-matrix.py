#!/usr/bin/env python3
"""P044: install a real Windows original-ROM native DAC/S3528 matrix dispatch.
Only modifies the QA test executable; leaves VST3 DSP and project ABI intact.
Requires prior P040 installation, and original ROM/OS media are never in CI.
"""
import argparse
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
HOST=UP/"tools/vst3_host_test.cpp"
HEADER=UP/"tools/p044_windows_native_original_adversarial.h"
SOURCE=ROOT/"tests/p044_windows_native_original_adversarial.h"

def once(s,old,new,label):
    count=s.count(old)
    if count!=1:
        raise RuntimeError(f"P044 {label}: expected one anchor, found {count}")
    return s.replace(old,new,1)

def patch(s):
    if "original-windows-native-p044-matrix" in s:
        raise RuntimeError("P044 dispatch already installed; refusing duplicate")
    s=once(s,
        '#include "p040_windows_original_adversarial.h"',
        '#include "p040_windows_original_adversarial.h"\n'
        '#include "p044_windows_native_original_adversarial.h"',
        "original Windows host header")
    s=once(s,
        '    if(argc>5&&std::string(argv[5])=="original-windows-p040-matrix"){',
        '''    if(argc>5&&std::string(argv[5])=="original-windows-native-p044-matrix"){
        // Genuine owner-only OS3.1, SAR, project bank, S3528 & native-DAC DSP.
        // No fake firmware/media, no direct RAM shortcut.
        const auto result=p044WindowsNativeOriginalAdversarial(
            factory,cid,host,rom,floppy,argc>4?argv[4]:"");
        module.reset();return result;
    }
    if(argc>5&&std::string(argv[5])=="original-windows-p040-matrix"){''',
        "owner-native COM dispatch")
    return s

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    if not SOURCE.is_file():
        raise RuntimeError("P044 native owner matrix source missing")
    base=HOST.read_text(encoding="utf-8")
    updated=patch(base)
    if args.verify:
        print("P044 original-Windows native DAC + S3528 host source anchors PASS")
    else:
        HOST.write_text(updated,encoding="utf-8",newline="\n")
        shutil.copyfile(SOURCE,HEADER)
        print("P044 owner-only native DAC matrix installed (no ROM in GitHub)")
if __name__=="__main__":
    main()
