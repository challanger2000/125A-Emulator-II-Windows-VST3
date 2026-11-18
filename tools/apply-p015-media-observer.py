#!/usr/bin/env python3
"""P015 original EII firmware floppy/HDD read activity invalidates stale bank claim.

After P014. Media reads are evidence that a live bank *may* have changed,
not evidence of a complete bank-load. Preserve real DISK7-only commits.
Source-pinned to upstream Tuth eii-emu; original emulator unchanged.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENG=UP/"src/vst3/plugin_engine.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,needle,replacement,name):
    n=s.count(needle)
    if n!=1:raise RuntimeError(f"P015 {name}: expected one exact anchor, found {n}")
    return s.replace(needle,replacement,1)

def patch(e):
    if "observeMediaReads()" in e:raise RuntimeError("P015 overlay already applied")
    for marker in ("ProjectSaveFrame projectSaveFrame()const",
                   "bankNeedsSnapshot_.store(s.bankPendingCapture",
                   "void saveCurrentBankInProject()",
                   "void cancelWavStep()"):
        if marker not in e:raise RuntimeError("P015 requires P014 owner source: "+marker)
    e=one(e,
        '#include "125a_media_safety.h"',
        '#include "125a_media_safety.h"\n#include "125a_live_media_watch.h"',
        "observed source header")
    e=one(e,
        '    bool manualBankCommit_=false;',
        '    bool manualBankCommit_=false;\n'
        '    portable::LiveMediaWatch bankMediaWatch_;',
        "original firmware read watch")
    e=one(e,
        '''    void bankStep(){''',
        '''    void observeMediaReads(){
        if(!machine_)return;
        const auto mode=machine_->channel0Mode();
        const std::uint64_t floppyReceived=machine_->diskSio.channels[0].rx.characters;
        const std::uint64_t hardDiskReceived=machine_->hardDisk?
            machine_->hardDisk->bytesRead:0;
        // Only the original firmware's ACTUAL input transactions count;
        // track 0 rotation alone is not evidence of a bank transfer.
        if(!bankMediaWatch_.observe(
              presetDisplayed(),mode.known&&mode.high,
              floppyReceived,hardDiskReceived))return;
        // Conservatively warn after firmware reads; whether it loaded a
        // different bank cannot be decided from a disk transaction alone.
        if(!bankNeedsSnapshot_.exchange(true,std::memory_order_acq_rel)&&
           !projectBusy_.load(std::memory_order_acquire)&&
           !manualBankCommit_){
            error_="Original firmware accessed floppy/HDD or entered SAMPLE. "
                   "Current live bank may differ from the last saved song bank. "
                   "Capture the current RAM bank via DISK 7 and save the song.";
        }
    }
    void bankStep(){''',
        "only firmware read activity dirties last committed bank")
    e=one(e,
        '''                machine_->run(n);
                wavStep();
                cancelWavStep();
                bankStep();''',
        '''                machine_->run(n);
                wavStep();
                cancelWavStep();
                // Observe before a successful firmware DISK7 commit clears
                // the dirty marker for this SAME batch of hardware clocks.
                observeMediaReads();
                bankStep();''',
        "sample before original DISK7 commit")
    e=one(e,
        '''            contacts_={};media_=media;error_=rescued;
            if(bootSelectedBank){''',
        '''            contacts_={};media_=media;error_=rescued;
            // Machine replacement invalidates all prior SIO/HDD counters.
            bankMediaWatch_.reset();
            // A newly selected original HDD/floppy file can contain programs
            // without any embedded project bank. It is an external
            // dependency, not a guaranteed DAW song snapshot.
            if(!embeddedBank_&&(!c.hdd.empty()||!c.floppy.empty()))
                bankNeedsSnapshot_.store(true,std::memory_order_release);
            if(bootSelectedBank){''',
        "mark external bank media at original boot")
    return e

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P015 original core SHA mismatch: "+sha)
    source=ENG.read_text(encoding="utf-8")
    target=patch(source)
    if args.verify:
        print("P015 firmware HDD and SIO live-bank guards: exact anchors PASS")
        return
    shutil.copyfile(ROOT/"src/125a_live_media_watch.h",UP/"src/125a_live_media_watch.h")
    ENG.write_text(target,encoding="utf-8",newline="\n")
    print("P015 firmware-disk activity observer installed on single machine owner thread")

if __name__=="__main__":main()
