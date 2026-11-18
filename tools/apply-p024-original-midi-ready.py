#!/usr/bin/env python3
"""P024: original firmware P01 appears before original SCN2651 MIDI is ready.

Genuine private ROM + original EII Choir .emuiifd boot on the pinned
original engine: first P01 at 44.31 virtual s (49.01 wall s),
then original MIDI receiver enabled and full "P01 EII Choir" at
44.33 virtual s (49.02 wall s); original MIDI & PCM subsequently PASS.

P021 cut over at first Pxx, exposing a brief but real unplayable window.
Keep the host gate closed until BOTH Pxx and original SCN2651 receiver
are ready; never fake it or bypass firmware. No ROM/audio engine changes.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENG=UP/"src/vst3/plugin_engine.h"
EDITOR=UP/"src/vst3/plugin_editor.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"P024 {label}: expected one exact anchor, got {n}")
    return s.replace(a,b,1)

def patch(e,v):
    for mark in ("bool advanceAutonomousBoot(){",
                 "bootMidiDiscarded_.store(0,std::memory_order_relaxed);",
                 "portable::insertDelayedFloppy(floppyHeld_,machine_->main.cpu.pc)",
                 "bootClock_.observe(", "bool autonomousBoot=false;"):
        if mark not in e:raise RuntimeError("P024 requires P022: "+mark)
    if "originalFirmwareMidiReady(" in e:raise RuntimeError("P024 already installed")
    e=one(e,
        '#include "125a_preboot_event_policy.h"',
        '#include "125a_preboot_event_policy.h"\n#include "125a_original_firmware_midi_ready.h"',
        "MIDI receiver firmware readiness include")
    e=one(e,
        '''    bool autonomousBoot=false;std::uint64_t bootMidiDiscarded=0;''',
        '''    bool autonomousBoot=false;std::uint64_t bootMidiDiscarded=0;
    bool bootMidiPending=false; // original LCD Pxx exists, SCN2651 not ready yet''',
        "diagnostic staging for first-Pxx before MIDI UART")
    e=one(e,
        '''        if(presetDisplayed()){
            // The native DSP worker's boot blocks must finish before the''',
        '''        // The original ROM may show P01 BEFORE the receiver's SCN2651
        // command/mode bits enable 31,250-baud MIDI. Only the original
        // firmware can decide when the instrument is truly host playable.
        if(portable::originalFirmwareMidiReady(
              presetDisplayed(),machine_->midiSerial.enabled())){
            // The native DSP worker's boot blocks must finish before the''',
        "true first playable original firmware gating")
    e=one(e,
        '''        s.autonomousBoot=autonomousBoot_.active();
        s.bootMidiDiscarded=bootMidiDiscarded_.load(std::memory_order_relaxed);
        // Real wall time vs virtual original 4 MHz clock;''',
        '''        s.autonomousBoot=autonomousBoot_.active();
        s.bootMidiDiscarded=bootMidiDiscarded_.load(std::memory_order_relaxed);
        s.bootMidiPending=autonomousBoot_.active()&&machine_&&
            presetDisplayed()&&!machine_->midiSerial.enabled();
        // Real wall time vs virtual original 4 MHz clock;''',
        "observed original firmware MIDI init state in Status")
    e=one(e,
        '''                presetDisplayed(),!next.floppy.idle||!next.hdd.idle,halted_);''',
        '''                portable::originalFirmwareMidiReady(
                    presetDisplayed(),machine_->midiSerial.enabled()),
                !next.floppy.idle||!next.hdd.idle,halted_);''',
        "P020 boot timestamp is true audible MIDI readiness, not early Pxx")
    v=one(v,
        '''         <<L"; MIDI during boot ignored: "<<s.bootMidiDiscarded
         <<L"\\nFirmware boot: "''',
        '''         <<L"; MIDI during boot ignored: "<<s.bootMidiDiscarded
         <<L"\\nOriginal MIDI initialization: "<<
             (s.bootMidiPending?L"LCD Pxx visible but SCN2651 NOT READY":
                L"No early Pxx/MIDI receiver mismatch")
         <<L"\\nFirmware boot: "''',
        "clearly display observed Pxx-but-unready condition in advanced Status")
    return e,v

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P024 pinned original firmware source mismatch")
    dst=patch(ENG.read_text(encoding="utf-8"),
              EDITOR.read_text(encoding="utf-8"))
    if a.verify:
        print("P024 authentic original ROM Pxx and SCN2651 two-stage readiness anchors: PASS")
        return
    shutil.copyfile(ROOT/"src/125a_original_firmware_midi_ready.h",
                    UP/"src/125a_original_firmware_midi_ready.h")
    for path,s in zip((ENG,EDITOR),dst):
        path.write_text(s,encoding="utf-8",newline="\n")
    print("P024 original MIDI-safe DAW startup handoff integrated")

if __name__=="__main__":main()
