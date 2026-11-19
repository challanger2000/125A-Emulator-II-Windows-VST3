#!/usr/bin/env python3
"""P036: replace demonstrably stale machine report claims about original SAR.

Pinned upstream has already implemented the MC14559B register, channel-0
input analog loop, comparator, DMA/INI, Z80 WAIT and real DRAM storage.
The original report incorrectly claims they are entirely unimplemented.
Keep absolute silicon/analog calibration explicitly OPEN.
"""
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
MACHINE=UP/"src/machine.cpp"

def one(text,old,new,label):
    count=text.count(old)
    if count!=1:raise RuntimeError(f"P036 {label}: expected exactly one source anchor, found {count}")
    return text.replace(old,new,1)

def patch(s):
    if "Original sample input 7-42/7-43" in s:
        raise RuntimeError("P036 already installed")
    s=one(s,
        '    o<<"(digital latches; channel0 MODE/SAR and analog conversion absent)\\n";',
        '''    o<<"(digital latches; channel0 MODE/SAR and nominal analog input are modeled; physical calibration OPEN)\\n";
    const auto mode=channel0Mode();
    o<<"Original sample input 7-42/7-43: IMODE=";
    if(mode.known)o<<mode.high;else o<<"unknown";
    const auto sarEoc=sampleSar.eoc();
    o<<" sample reads="<<sampleReads<<" unknown reads="<<sampleUnknownReads
     <<" SAR conversions="<<sampleSar.conversions
     <<" SAR comparator unknown="<<sampleAnalog.unknownComparisons
     <<" SAR WAIT clocks="<<sampleWaitClocks
     <<" analog input steps="<<sampleAnalog.chainSteps
     <<" amplifier rail clips="<<sampleAnalog.railClips
     <<" EOC=";
    if(sarEoc.known)o<<sarEoc.high;else o<<"unknown";
    o<<" (schematic-derived, uncalibrated input amplifier/ADC/DAC)\\n";''',
        "truthful original SAR diagnostics")
    s=one(s,
        '''    o<<"UNIMPLEMENTED: other SIO formats/TX interrupts and general DMA search/burst/read-register modes outside the floppy subset, physical BUSACK/subcycle calibration, sample-recording/SAR DRAM writes, calibrated sample DAC/filter/VCA, PIO mode-0/1 strobes and mode-3 bit interrupts.\\n";''',
        '''    o<<"UNIMPLEMENTED/UNCALIBRATED: other SIO formats/TX interrupts and general DMA search/burst/read-register modes outside the floppy subset, physical BUSACK/subcycle calibration, actual analog sample-input gain/sampling-offset/ADC silicon and original board calibration, calibrated playback DAC/filter/VCA, PIO mode-0/1 strobes and mode-3 bit interrupts.\\n";''',
        "remove obsolete missing original analog SAR claim")
    s=one(s,
        '''    if(!serialTx.empty()) o<<"2651 TX (register-level capture, no serial-bit timing):\\n"<<serialTx<<"\\n";''',
        '''    if(!serialTx.empty()) o<<"2651 TX (modeled 31250 baud character completion; physical serial-bit edges not synthesized):\\n"<<serialTx<<"\\n";''',
        "truthful P033 original MIDI OUT TX diagnostic")
    return s

def main():
    a=argparse.ArgumentParser();a.add_argument("--verify",action="store_true");args=a.parse_args()
    head=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if head!=PIN:raise RuntimeError("P036 upstream pin mismatch: "+head)
    old=MACHINE.read_text(encoding="utf-8")
    if "txCharacterTicks=1280" not in (UP/"src/midi_serial.h").read_text(encoding="utf-8"):
        raise RuntimeError("P036 must run after P033 serial hardware integration")
    new=patch(old)
    if args.verify:print("P036 real sample hardware reporting original SAR/ADC and accurate MIDI TX anchors PASS")
    else:
        MACHINE.write_text(new,encoding="utf-8",newline="\n")
        print("P036 original SAR/dram/analog diagnostics corrected; missing full hardware calibration remains OPEN")
if __name__=="__main__":main()
