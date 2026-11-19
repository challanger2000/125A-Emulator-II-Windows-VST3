#!/usr/bin/env python3
"""Adversarial P035 code integration guard. Test-only assertions don't prove
full ROM/MIDI transmission; actual synthetic Z80 machine run is separate.
"""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENG=(ROOT/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
BYTES=(ROOT/"upstream/eii-emu/src/125a_original_midi_out.h").read_text(encoding="utf-8")
s=importlib.util.spec_from_file_location("p035_gap",ROOT/"tools/apply-p035-midi-out-gap-recovery.py")
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

for token in (
    "std::uint8_t gap=0;",
    "Only the consumer resets its parser",
):
    assert token in BYTES,token
for token in (
    "bool originalMidiOutGapPending_=false;",
    "if(b.gap)originalMidiParser_.reset();",
    "std::uint8_t(originalMidiOutGapPending_)",
    "originalMidiOutGapPending_=true;",
    "originalMidiOutGapPending_=false;",
    "originalMidiOutDrops_.fetch_add(1,std::memory_order_relaxed);",
):
    assert token in ENG,token
assert ENG.count("originalMidiOutGapPending_=true;")==1
assert ENG.count("if(b.gap)originalMidiParser_.reset();")==1
assert ENG.count("originalMidiOutGapPending_=false;")==3, "owner declaration, post-success, boot reset"
assert ENG.index("if(b.gap)originalMidiParser_.reset();") < ENG.index("if(originalMidiParser_.feed(b.value,msg))")
assert ENG.index("originalMidiOutDrops_.fetch_add(1,std::memory_order_relaxed);") < ENG.index("originalMidiOutGapPending_=true;")
# Existing mandatory original-firmware producer and earlier P034 source still live.
assert "machine_->midiSerial.popTx(completed)" in ENG
assert "SpscQueue<midiout::Byte,8192> originalMidiOut_" in ENG
assert "originalMidiParser_.reset();" in ENG
for body,patch in ((ENG,p.patch_engine),(BYTES,p.patch_header)):
    try:patch(body)
    except RuntimeError:pass
    else:raise AssertionError("duplicate P035 overflow safety patch unexpectedly accepted")
print("P035 real SCN2651 producer -> bounded SPSC gap -> post-loss MIDI reset ordering and duplicate mutants PASS")
