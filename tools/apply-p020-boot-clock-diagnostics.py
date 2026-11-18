#!/usr/bin/env python3
"""P020: make the original host-clock boot bottleneck measurable.

The existing EII instrument executes hardware ticks up to hostTarget().
This patch observes wall clock, virtual 4MHz ticks, floppy/HDD progress and
lack of callbacks; unlike arbitrary CPU overclock, it NEVER edits original
chip, disk, audio, DSP, firmware or MIDI scheduling.
"""
import argparse
import shutil
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENGINE=UP/"src/vst3/plugin_engine.h"
EDITOR=UP/"src/vst3/plugin_editor.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,old,new,reason):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"P020 {reason}: {n} matching anchors, expected one")
    return s.replace(old,new,1)

def patch(e,v):
    if "bootClock_.begin(" in e:raise RuntimeError("P020 already applied")
    for required in ("originalBootBatch_.reset();","void observeMediaReads()",
                     "captureHddForProject()", "wavKeyMap_.reset();"):
        if required not in e:raise RuntimeError("P020 requires P019: "+required)

    e=one(e,
        '#include "125a_original_boot_batch.h"',
        '#include "125a_original_boot_batch.h"\n#include "125a_boot_clock_diagnostics.h"',
        "diagnostic boot clock header")
    e=one(e,
        '''    bool ownerMmcss=false,ownerHighQos=false,highResolutionWait=false,fastPanelActive=false,memory1mbActive=false;''',
        '''    bool ownerMmcss=false,ownerHighQos=false,highResolutionWait=false,fastPanelActive=false,memory1mbActive=false;
    portable::BootClockSnapshot boot; // owner-produced, no RT work''',
        "host status boot clock structure")
    e=one(e,
        '    portable::OriginalBootBatch originalBootBatch_;',
        '''    portable::OriginalBootBatch originalBootBatch_;
    portable::BootClockDiagnostics bootClock_;''',
        "single owner boot clock tracker")
    e=one(e,
        '''            originalBootBatch_.reset();
            midiTools_.wheelBridge=c.midiWheels;''',
        '''            originalBootBatch_.reset();
            const auto bootNowMs=std::uint64_t(std::chrono::duration_cast<
                std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count());
            bootClock_.begin(bootNowMs,machine_->ticks,
                tickOf(hostTarget_.load(std::memory_order_acquire)),
                machine_->diskSio.channels[0].rx.characters,
                machine_->hardDisk?machine_->hardDisk->bytesRead:0);
            midiTools_.wheelBridge=c.midiWheels;''',
        "start stopwatch at original machine boot")
    e=one(e,
        '''        if(samplingTrace_.recording()){''',
        '''        s.recallProgram=recallProgram_.load();s.recallPending=recallPending_;
        // Real wall time vs virtual original 4 MHz clock; a stopped host
        // target is distinct from slow firmware disk transfers or CPU load.
        if(machine_){
            const auto nowMs=std::uint64_t(std::chrono::duration_cast<
                std::chrono::milliseconds>(now.time_since_epoch()).count());
            s.boot=bootClock_.observe(
                nowMs,machine_->ticks,
                tickOf(hostTarget_.load(std::memory_order_acquire)),
                machine_->diskSio.channels[0].rx.characters,
                machine_->hardDisk?machine_->hardDisk->bytesRead:0,
                presetDisplayed(),!next.floppy.idle||!next.hdd.idle,halted_);
        }else s.boot=bootClock_.snapshot();
        if(samplingTrace_.recording()){''',
        "publish original boot diagnostic only on machine owner")
    v=one(v,
        '<<L"\\nLate frames (realtime underruns): "',
        '''<<L"\\nFirmware boot: "<<wide(portable::bootStageName(s.boot.stage))
         <<L"\\nBoot wall / virtual: "<<double(s.boot.wallMs)/1000.0
         <<L" s / "<<double(s.boot.virtualTicks)/4e6<<" s"
         <<L"; effective boot speed "<<double(s.boot.realtimePermille)/10.0<<"%"
         <<L"\\nHost audio clock inactive: "<<double(s.boot.hostInactiveMs)/1000.0
         <<L" s; machine inactive: "<<double(s.boot.emulatorInactiveMs)/1000.0<<" s"
         <<L"; floppy / HDD bytes during boot: "<<s.boot.floppyBytes<<" / "<<s.boot.hddBytes
         <<L"\\nLate frames (realtime underruns): "''',
        "show host vs emulated clock diagnostics before existing performance stats")
    return e,v

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    a=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P020 pinned original firmware/core SHA mismatch")
    updated=patch(ENGINE.read_text(encoding="utf-8"),
                  EDITOR.read_text(encoding="utf-8"))
    if a.verify:
        print("P020 original hardware and DAW host clock instrumentation anchors: PASS")
        return
    shutil.copyfile(ROOT/"src/125a_boot_clock_diagnostics.h",UP/"src/125a_boot_clock_diagnostics.h")
    for path,body in zip((ENGINE,EDITOR),updated):
        path.write_text(body,encoding="utf-8",newline="\n")
    print("P020 original boot wall/virtual/media/DAW-clock diagnostics installed")
if __name__=="__main__":main()
