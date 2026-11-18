#!/usr/bin/env python3
"""P024 genuine original-ROM evidence: LCD Pxx precedes MIDI UART enabled."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
e=(root/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
v=(root/"upstream/eii-emu/src/vst3/plugin_editor.h").read_text(encoding="utf-8")
h=(root/"upstream/eii-emu/src/125a_original_firmware_midi_ready.h").read_text()
assert '#include "125a_original_firmware_midi_ready.h"' in e
assert 'bool bootMidiPending=false;' in e
a=e[e.index("bool advanceAutonomousBoot(){"):e.index("bool quitRequested()",e.index("bool advanceAutonomousBoot(){"))]
assert 'if(portable::originalFirmwareMidiReady(' in a
assert 'presetDisplayed(),machine_->midiSerial.enabled())){' in a
assert a.index('if(portable::originalFirmwareMidiReady(')<a.index('handoffAutonomousBoot(true)')
assert a.index('if(floppyBacking_)installFloppy(*machine_,floppyBacking_);') < a.index('if(portable::originalFirmwareMidiReady(')
assert 'handoffAutonomousBoot(false)' in a
assert 'runTicks(portable::AutonomousBootTimeline::quantum(nonlinear()))' in a
assert "s.bootMidiPending=autonomousBoot_.active()&&machine_&&" in e
assert "presetDisplayed()&&!machine_->midiSerial.enabled();" in e
assert "portable::originalFirmwareMidiReady(" in e[e.index('s.boot=bootClock_.observe('):]
assert 'LCD Pxx visible but SCN2651 NOT READY' in v
assert 'return presetDisplayed&&originalScn2651Enabled;' in h
assert "void Machine::run(std::uint64_t cycles)" in (root/"upstream/eii-emu/src/machine.cpp").read_text()
print("P024 original-ROM-reproducible first-Pxx-then-MIDI VST3 host gate source PASS")
