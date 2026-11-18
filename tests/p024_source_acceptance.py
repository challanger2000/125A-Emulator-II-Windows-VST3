#!/usr/bin/env python3
"""Source-level regression of original-ROM hardware readiness.
The private ROM/disk/Choir PCM is intentionally NOT in public CI.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
e=(root/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
h=(root/"upstream/eii-emu/src/125a_original_midi_ready.h").read_text(encoding="utf-8")
assert '#include "125a_original_midi_ready.h"' in e
assert 'portable::firmwarePlayable(' in e
assert 'presetDisplayed(),machine_->midiSerial.enabled());' in e
assert 'bool originalPlayable()const noexcept{' in e
assert 'return machine_&&portable::firmwarePlayable(' in e
run=e[e.index("void runTicks("):e.index("bool quitRequested()",e.index("void runTicks("))]
assert 'if(originalPlayable()){const int pc=recallProgram_.load();recallPending_=false;' in run
assert 'if(presetDisplayed()){const int pc=recallProgram_.load();' not in run
boot=e[e.index("bool advanceAutonomousBoot(){"):
       e.index("bool quitRequested()",e.index("bool advanceAutonomousBoot(){"))]
assert 'if(originalPlayable()){' in boot
assert 'if(presetDisplayed()){' not in boot
assert boot.index('if(originalPlayable()){')<boot.index('handoffAutonomousBoot(true);')
assert 'originalPlayable(),!next.floppy.idle||!next.hdd.idle,halted_);' in e
assert 'first Pxx' in h
assert "void Machine::run(std::uint64_t cycles)" in (root/"upstream/eii-emu/src/machine.cpp").read_text()
print("P024 first real LCD Pxx + firmware MIDI UART gating/recalled program/boot status PASS")
