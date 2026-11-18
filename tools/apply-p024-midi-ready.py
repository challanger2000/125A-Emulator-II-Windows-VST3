#!/usr/bin/env python3
"""P024 real original EII boot readiness = first Pxx AND original UART ready.

The user's private original ROM/Choir disk boot measured Pxx at 49.01s,
but SCN2651 MIDI receiver was enabled only at 49.02s. P021/P022 had
handed audio+MIDI to the host a few milliseconds early. Fix boot handoff,
project preset recall, and boot-ready telemetry consistently; no fake
delay, ROM alteration, MIDI injection or sample/CPU clock manipulation.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENG=UP/"src/vst3/plugin_engine.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,a,b,name):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"P024 {name}: expected 1 source anchor, got {n}")
    return s.replace(a,b,1)

def patch(e):
    for need in ("bool advanceAutonomousBoot(){",
                 "s.boot=bootClock_.observe(", "recallPending_",
                 "if(presetDisplayed()){", "midiSerial",
                 "void handoffAutonomousBoot(bool playable){"):
        if need not in e:raise RuntimeError("P024 requires verified P022 overlay: "+need)
    if "#include \"125a_original_midi_ready.h\"" in e:
        raise RuntimeError("P024 applied twice")
    e=one(e,
        '#include "125a_preboot_event_policy.h"',
        '#include "125a_preboot_event_policy.h"\n#include "125a_original_midi_ready.h"',
        "include shared actual firmware MIDI ready predicate")
    e=one(e,
        '''    bool presetDisplayed()const{
        if(!machine_||!machine_->lcd.display)return false;const auto l=machine_->lcd.line(0);
        return l.size()>=3&&l[0]=='P'&&std::isdigit(static_cast<unsigned char>(l[1]))&&std::isdigit(static_cast<unsigned char>(l[2]));
    }''',
        '''    bool presetDisplayed()const{
        if(!machine_||!machine_->lcd.display)return false;const auto l=machine_->lcd.line(0);
        return l.size()>=3&&l[0]=='P'&&std::isdigit(static_cast<unsigned char>(l[1]))&&std::isdigit(static_cast<unsigned char>(l[2]));
    }
    bool originalPlayable()const noexcept{
        return machine_&&portable::firmwarePlayable(
            presetDisplayed(),machine_->midiSerial.enabled());
    }''',
        "original LCD plus actual SCN2651 ready gate")
    e=one(e,
        '''                    if(presetDisplayed()){const int pc=recallProgram_.load();recallPending_=false;''',
        '''                    if(originalPlayable()){const int pc=recallProgram_.load();recallPending_=false;''',
        "do not send recalled program before original UART ready")
    e=one(e,
        '''        if(presetDisplayed()){
            // The native DSP worker's boot blocks must finish before the''',
        '''        if(originalPlayable()){
            // The native DSP worker's boot blocks must finish before the''',
        "do not open audio gate until actual original firmware MIDI ready")
    e=one(e,
        '''                presetDisplayed(),!next.floppy.idle||!next.hdd.idle,halted_);''',
        '''                originalPlayable(),!next.floppy.idle||!next.hdd.idle,halted_);''',
        "first genuinely playable LCD+MIDI freezes measured boot time")
    return e

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    a=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P024 original ROM source pinned SHA mismatch")
    patched=patch(ENG.read_text(encoding="utf-8"))
    if a.verify:
        print("P024 original MIDI ready and first Pxx handoff anchors PASS")
        return
    shutil.copyfile(ROOT/"src/125a_original_midi_ready.h",
                    UP/"src/125a_original_midi_ready.h")
    ENG.write_text(patched,encoding="utf-8",newline="\n")
    print("P024 original EII first playable Pxx + SCN2651 UART readiness integrated")
if __name__=="__main__":main()
