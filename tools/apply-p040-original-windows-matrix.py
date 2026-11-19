#!/usr/bin/env python3
"""P040 Windows x64 real original OS3.1 VST3 COM negative and rate matrix.
Install AFTER P038 and P039 overlays; do not modify the original EII core.
"""
import argparse
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
HOST=UP/"tools/vst3_host_test.cpp"
HEADER=UP/"tools/p040_windows_original_adversarial.h"

def one(text,anchor,replace,label):
    if text.count(anchor)!=1:
        raise RuntimeError("P040 "+label+" source drift: found "+
                           str(text.count(anchor))+" anchors, required 1")
    return text.replace(anchor,replace,1)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--verify",action="store_true")
    args=a.parse_args()
    text=HOST.read_text(encoding="utf-8")
    if "p040WindowsOriginalAdversarial(" in text:
        raise RuntimeError("P040 test already applied")
    text=one(text,
        '#include "p038_windows_original_host_capture.h"',
        '#include "p038_windows_original_host_capture.h"\n'
        '#include "p040_windows_original_adversarial.h"',
        "original Windows VST3 host test includes")
    anchor='    if(argc>5&&std::string(argv[5])=="original-windows-live-record"){'
    text=one(text,anchor,
        '''    if(argc>5&&std::string(argv[5])=="original-windows-p040-matrix"){
        // argv2 = owner ROM dir; argv3 = OS3.1 floppy; argv4 = Choir floppy.
        // Exact same authentic VST3 COM component as the P039 owner test.
        const auto result=p040WindowsOriginalAdversarial(factory,cid,host,rom,floppy,
                                                         argc>4?argv[4]:"");
        module.reset();return result;
    }
'''+anchor, "original Windows COM matrix dispatch")
    if args.verify:
        print("P040 source-pinned Windows VST3 COM 44.1/48k + negative matrix anchors: PASS")
        return
    if not (ROOT/"tests/p040_windows_original_adversarial.h").is_file():
        raise RuntimeError("P040 original Windows private matrix source missing")
    HOST.write_text(text,encoding="utf-8",newline="\n")
    shutil.copyfile(ROOT/"tests/p040_windows_original_adversarial.h",HEADER)
    print("P040 original firmware Windows VST3 COM matrix installed, no ROMs in CI")

if __name__=="__main__":
    main()
