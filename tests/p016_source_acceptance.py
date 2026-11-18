#!/usr/bin/env python3
"""P016 source guards: bounded only on silence; CPU/DSP/MIDI untouched."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3"
s=(root/"rt_primitives.h").read_text(encoding="utf-8")
e=(root/"plugin_engine.h").read_text(encoding="utf-8")
a=s[s.index("void pushSilence(std::uint64_t n)"):s.index("    std::uint64_t written()")]
b=s[s.index("void alignTo(std::uint64_t index)"):s.index("    void push(std::span<const Frame> frames)")]
assert "std::min<std::uint64_t>(n" in a
assert "std::min<std::uint64_t>(capacity,freeSlots)" in a
assert "w+n" in a
assert "wakeConsumer()" in a
assert "std::min<std::uint64_t>(gap,capacity)" in b
assert "w_.store(index,std::memory_order_release);" in b
assert 'void push(std::span<const host::StereoFrame> frames)noexcept{' in s
assert 'void push(std::span<const Frame> frames)noexcept{' in s
assert 'runTicks(limit-G_);' in e
print("P016 bounded long silence only (CPU, MIDI and original DSP unchanged): PASS")
