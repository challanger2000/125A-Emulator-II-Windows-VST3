#!/usr/bin/env python3
"""P019 first-original-preset-only boot scheduling, no virtual CPU skip."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
e=(root/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
h=(root/"upstream/eii-emu/src/125a_original_boot_batch.h").read_text(encoding="utf-8")
assert '#include "125a_original_boot_batch.h"' in e
assert "portable::OriginalBootBatch originalBootBatch_;" in e
assert "originalBootBatch_.reset();" in e
assert "if(!originalBootBatch_.isReady()&&presetDisplayed())" in e
assert "originalBootBatch_.ready(); // original firmware reached playable Pxx" in e
assert "originalBootBatch_.ready();" in e[e.index("void contact(unsigned i,bool pressed)"):e.index("void applyMidi(",e.index("void contact(unsigned i,bool pressed)"))]
a=e[e.index("bool advance()"):e.index("void publish(bool force)")]
assert "originalBootBatch_.quantum(dsp,urgent,unsafeFast)" in a
assert "const bool unsafeFast=(!producing())||sampling||" in a
assert "wavCapture_.active()||bankSave_.active()" in a
assert "projectBusy_.load(std::memory_order_acquire)" in a
assert "auto limit=std::min(target,G_+step);" in a
assert "tickOf(e->pos)" in a
assert "runTicks(limit-G_);" in a
assert "gOffset_+=newG-G_" in a, "original realtime rebase not touched"
assert "quantum=20000,fineQuantum=4000,dspBlockTicks=8000" in e
assert "bootBasic=3*quantumNormal" in h and "bootDsp=6*dspBlock" in h
assert 'void Machine::run(std::uint64_t cycles)' in (root/"upstream/eii-emu/src/machine.cpp").read_text()
print("P019 original EII first-Pxx scheduler with exact host MIDI and audio safeties PASS")
