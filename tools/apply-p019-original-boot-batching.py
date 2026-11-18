#!/usr/bin/env python3
"""P019: reduce costly original EII Machine::run call overhead during startup.

CPU/Z80/DRAM/DSP original source is untouched. Only the owner thread's
maximum scheduler quantum changes from 5-6ms to 12-15ms while booting.
An exact MIDI event position and host target still cut the quantum.
Urgent audio, original SAR/SAMPLE, bank save, active project import, and
every user panel press use the established 1-6ms scheduler immediately.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENGINE=UP/"src/vst3/plugin_engine.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,before,after,name):
    count=s.count(before)
    if count!=1:raise RuntimeError(f"P019 {name}: {count} anchors, need exactly one")
    return s.replace(before,after,1)

def patch(s):
    if "originalBootBatch_" in s:raise RuntimeError("P019 already installed")
    for marker in ("ProjectSaveFrame projectSaveFrame()const",
                   "captureHddForProject()", "wavKeyMap_.reset();",
                   "void observeMediaReads()"):
        if marker not in s:raise RuntimeError("P019 requires full P018 overlays: "+marker)
    s=one(s,'#include "125a_wav_c3_keyboard.h"',
        '#include "125a_wav_c3_keyboard.h"\n#include "125a_original_boot_batch.h"',
        "original boot scheduler include")
    s=one(s,'    portable::WavC3Keyboard wavKeyMap_; // owner-only note pairing',
        '''    portable::WavC3Keyboard wavKeyMap_; // owner-only note pairing
    portable::OriginalBootBatch originalBootBatch_;''',
        "owner boot-only batching guard")
    s=one(s,
        '''    void contact(unsigned i,bool pressed){
        if(!machine_||i>=30)return;''',
        '''    void contact(unsigned i,bool pressed){
        if(!machine_||i>=30)return;
        // Real user interaction must never be delayed by an expanded boot
        // quantum even if firmware has not yet reached the Pxx display.
        originalBootBatch_.ready();''',
        "manual panel disables boost permanently until next real boot")
    s=one(s,
        '''            midiTools_.resetInputState();wavKeyMap_.reset();''',
        '''            midiTools_.resetInputState();wavKeyMap_.reset();
            originalBootBatch_.reset();''',
        "fresh original hardware reset re-arms boot batching")
    s=one(s,
        '''        flushThrottle();
        if(floppyHeld_''',
        '''        flushThrottle();
        if(!originalBootBatch_.isReady()&&presetDisplayed())
            originalBootBatch_.ready(); // original firmware reached playable Pxx
        if(floppyHeld_''',
        "stop boot optimization at first playable preset")
    s=one(s,
        '''        const std::uint64_t step=urgent?(dsp?dspBlockTicks:fineQuantum):(dsp?3*dspBlockTicks:quantum);
        auto limit=std::min(target,G_+step);''',
        '''        // Repeated Machine::run() entry has measured high overhead.
        // Batch only the ORIGINAL 4 MHz clocks until the first Pxx, with
        // no sample/memory/midi bypass. Urgent audio, real SAMPLE and
        // original DISK7 use the old fine scheduler.
        const bool unsafeFast=(!producing())||sampling||
            wavCapture_.active()||bankSave_.active()||
            projectBusy_.load(std::memory_order_acquire);
        const std::uint64_t step=originalBootBatch_.quantum(dsp,urgent,unsafeFast);
        auto limit=std::min(target,G_+step);''',
        "bounded original boot quantum choice")
    return s

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P019 original EII machine source SHA mismatch")
    out=patch(ENGINE.read_text(encoding="utf-8"))
    if args.verify:
        print("P019 original firmware 4 MHz safe batching anchors: PASS")
        return
    shutil.copyfile(ROOT/"src/125a_original_boot_batch.h",UP/"src/125a_original_boot_batch.h")
    ENGINE.write_text(out,encoding="utf-8",newline="\n")
    print("P019 safe pre-preset owner batching installed (no CPU/DSP modifications)")

if __name__=="__main__":
    main()
