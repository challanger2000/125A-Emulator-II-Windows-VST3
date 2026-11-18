#!/usr/bin/env python3
"""P020 diagnostics do not overclock original Emulator II or shift MIDI/audio."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
engine=(root/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
editor=(root/"upstream/eii-emu/src/vst3/plugin_editor.h").read_text(encoding="utf-8")
original=(root/"upstream/eii-emu/src/machine.cpp").read_text(encoding="utf-8")
for v in (
    '#include "125a_boot_clock_diagnostics.h"',
    "portable::BootClockSnapshot boot; // owner-produced, no RT work",
    "portable::BootClockDiagnostics bootClock_;",
    "bootClock_.begin(bootNowMs,machine_->ticks,",
    "s.boot=bootClock_.observe(",
    "tickOf(hostTarget_.load(std::memory_order_acquire))",
    "presetDisplayed(),!next.floppy.idle||!next.hdd.idle,halted_",
    "originalBootBatch_.quantum(dsp,urgent,unsafeFast)",
):
    assert v in engine, "P020 missing boot owner telemetry "+v
for v in (
    'wide(portable::bootStageName(s.boot.stage))',
    "double(s.boot.virtualTicks)/4e6",
    "double(s.boot.wallMs)/1000.0",
    "double(s.boot.hostInactiveMs)/1000.0",
    "s.boot.floppyBytes",
):
    assert v in editor, "P020 missing diagnostic GUI "+v
boot=engine[engine.index("void bootNow(bool discard,bool fromState)"):
            engine.index("    // ---- input ----")]
assert boot.index("machine_=std::move(fresh)")<boot.index("bootClock_.begin(")
assert "bootClock_.begin(" not in engine[engine.index("void render("):engine.index("    // ---- Commands")]
assert engine[engine.index("bool advance()"):engine.index("void publish(bool force)")].count("runTicks(limit-G_);")==1
assert "while(cycles--)" in original,"original CPU loop must execute every tick"
assert "void Machine::run(std::uint64_t cycles)" in original
assert "bootClock_.observe" not in original, "never edit emulation core"
print("P020 original firmware/4MHz/host sound unchanged; boot clock only: PASS")
