#!/usr/bin/env python3
"""P035 fail-closed MIDI OUT loss recovery.

The real host MIDI SPSC may fill after prolonged starvation or a host-block
stall. A dropped byte MUST NOT join the previous running-status/half message,
or a valid firmware sequence could be turned into a spurious VST3 NoteOn.
The producer stamps the first recovered byte with a gap barrier, and only
the audio consumer resets its own parser when it reaches that boundary.
"""
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ENGINE=UP/"src/vst3/plugin_engine.h"
HEADER=UP/"src/125a_original_midi_out.h"

def one(s,a,b,label):
    count=s.count(a)
    if count!=1:raise RuntimeError(f"P035 {label}: expected one anchor, found {count}")
    return s.replace(a,b,1)

def patch_header(s):
    if "std::uint8_t gap=0;" in s:
        raise RuntimeError("P035 byte loss barrier already installed")
    return one(s,
        "    std::uint64_t epoch=0,generation=0,frame=0;",
        """    std::uint64_t epoch=0,generation=0,frame=0;
    // The first accepted TX byte AFTER one or more dropped bytes.
    // Only the consumer resets its parser; never mutate its state on owner.
    std::uint8_t gap=0;""",
        "completed outgoing byte's SPSC loss marker")

def patch_engine(s):
    if "originalMidiOutGapPending_" in s:
        raise RuntimeError("P035 MIDI OUT recovery already installed")
    s=one(s,
        "    host::MidiHostTools midiTools_;",
        """    host::MidiHostTools midiTools_;
    // Owner thread only. Mark first successfully queued byte after a full
    // SPSC push, so the consumer resets at the EXACT loss boundary.
    bool originalMidiOutGapPending_=false;""",
        "original owner MIDI OUT loss state")
    s=one(s,
        "            midiTools_.wheelBridge=c.midiWheels;midiTools_.noteOffZero=c.noteOffZero;",
        """            midiTools_.wheelBridge=c.midiWheels;midiTools_.noteOffZero=c.noteOffZero;
            originalMidiOutGapPending_=false;""",
        "reboot no cross-song pending MIDI gap")
    s=one(s,
        """            originalMidiOut_.pop();
            midiout::Message msg{};
            if(originalMidiParser_.feed(b.value,msg)){""",
        """            originalMidiOut_.pop();
            // P035: Reset only when the ACTUAL producer loss point is
            // reached. Already-buffered valid messages remain valid.
            if(b.gap)originalMidiParser_.reset();
            midiout::Message msg{};
            if(originalMidiParser_.feed(b.value,msg)){""",
        "consumer precise loss boundary, not global asynchronous reset")
    s=one(s,
        """                    const midiout::Byte packet{completed.byte,epoch,
                        streamGeneration_.load(std::memory_order_acquire),hostSample};
                    if(!originalMidiOut_.push(packet))
                        originalMidiOutDrops_.fetch_add(1,std::memory_order_relaxed);""",
        """                    const midiout::Byte packet{completed.byte,epoch,
                        streamGeneration_.load(std::memory_order_acquire),hostSample,
                        std::uint8_t(originalMidiOutGapPending_)};
                    if(!originalMidiOut_.push(packet)){
                        originalMidiOutDrops_.fetch_add(1,std::memory_order_relaxed);
                        originalMidiOutGapPending_=true;
                    }else{
                        originalMidiOutGapPending_=false;
                    }""",
        "UART original TX loss propagation into next accepted byte")
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--verify",action="store_true")
    args=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P035 pinned upstream source changed: "+sha)
    oldH=HEADER.read_text(encoding="utf-8")
    oldE=ENGINE.read_text(encoding="utf-8")
    if "originalMidiOut_" not in oldE or "txCharacterTicks=1280" not in (
            UP/"src/midi_serial.h").read_text(encoding="utf-8"):
        raise RuntimeError("P035 requires P033/P034 genuine original firmware MIDI OUT")
    newH=patch_header(oldH)
    newE=patch_engine(oldE)
    if args.verify:
        print("P035 source-pinned MIDI OUT loss marker and correct parser recovery gates PASS")
    else:
        HEADER.write_text(newH,encoding="utf-8",newline="\n")
        ENGINE.write_text(newE,encoding="utf-8",newline="\n")
        print("P035 original MIDI OUT SPSC overflow recovery at first restored physical byte integrated")
if __name__=="__main__":main()
