#!/usr/bin/env python3
"""P012 media validation overlay after P011. Never silently pad partial .EII banks."""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
FLOPPY=UP/"src/floppy_image_backing.h"
ENGINE=UP/"src/vst3/plugin_engine.h"
EDITOR=UP/"src/vst3/plugin_editor.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,old,new,name):
    found=s.count(old)
    if found!=1:raise RuntimeError(f"P012 {name}: {found} source anchors (expected one)")
    return s.replace(old,new,1)

def patch(f,e,v):
    if "canonicalEiiBankSize" in f or "inspectHdd" in e:
        raise RuntimeError("P012 already applied")
    if "cancelWavStep();" not in e:
        raise RuntimeError("P012 requires applied P011 firmware-cancel patch")
    f=one(f,'#include "hdd_image_file.h"',
        '#include "hdd_image_file.h"\n#include "125a_media_safety.h"',
        "bank validation include")
    f=one(f,
        '''   if(bytes.empty()||bytes.size()>EmuiiImage::imageBytes-bankOffset)throw std::runtime_error("EII bank import requires at most 494592 bytes.");''',
        '''   if(!portable::canonicalEiiBankSize(bytes.size()))
    throw std::runtime_error("Invalid .EII bank: expected exactly 485887 bytes. "
                             "Truncated/unknown variants cannot be silently padded.");''',
        "reject silently padded .EII")
    e=one(e,
        '#include "125a_firmware_cancel.h"',
        '#include "125a_firmware_cancel.h"\n#include "125a_media_safety.h"',
        "HDD diagnostics include")
    e=one(e,
        '''        const unsigned slots=bank::hddSlotCount(image.size());std::string report;unsigned next=0,written=0;''',
        '''        const auto info=portable::inspectHdd(image);
        if(info.unformatted)
            throw std::runtime_error("HDD is blank/unformatted: 0 usable bank slots. "
                "Boot the original HD OS 3.1 and use SPECIAL 22 to format the disk "
                "before importing .EII banks.");
        const unsigned slots=info.capacity;
        if(!info.available)
            throw std::runtime_error("Formatted HDD has no free bank slots; "
                "save a new disk copy or free space in the original firmware.");
        std::string report;unsigned next=0,written=0;''',
        "unformatted vs full media")
    v=one(v,
        '''AppendMenuW(hdd,MF_STRING,21,L"Create blank 20 MB HDD... (next boot)")''',
        '''AppendMenuW(hdd,MF_STRING,21,L"Create UNFORMATTED 20 MB HDD... (SPECIAL 22 needed)")''',
        "honest media label")
    v=one(v,
        r'''ask(L"Blank HDD created and selected.\n\nSelect the HD OS floppy, Boot / reset (main23.bin), then use SPECIAL 22 to format it.",L"HDD",MB_ICONINFORMATION);''',
        r'''ask(L"UNFORMATTED HDD created and selected.\n\nUsable bank slots: 0 of 46 until the original firmware formats it.\n\n1. Boot the original HD OS 3.1 (main23.bin).\n2. Run SPECIAL 22 FORMAT in the original Emulator II.\n3. Only then import .EII banks.\n\nThe image is not ready for banks yet.",L"HDD setup",MB_ICONINFORMATION);''',
        "HDD clear setup steps")
    return f,e,v

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError(f"P012 wrong pinned upstream: {sha}")
    f,e,v=patch(FLOPPY.read_text(encoding="utf-8"),
                ENGINE.read_text(encoding="utf-8"),
                EDITOR.read_text(encoding="utf-8"))
    if a.verify:
        print("P012 original media safety source anchors: PASS")
        return
    shutil.copyfile(ROOT/"src/125a_media_safety.h",UP/"src/125a_media_safety.h")
    for p,s in ((FLOPPY,f),(ENGINE,e),(EDITOR,v)):
        p.write_text(s,encoding="utf-8",newline="\n")
    print("P012 strict .EII media and HDD format diagnostics applied")

if __name__=="__main__":main()
