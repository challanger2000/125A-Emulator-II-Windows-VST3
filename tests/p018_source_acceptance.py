#!/usr/bin/env python3
"""P018 original hardware firmware untouched; per-song host-C3 mapping."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3"
e=(root/"plugin_engine.h").read_text(encoding="utf-8")
s=(root/"plugin_state.h").read_text(encoding="utf-8")
v=(root/"plugin_editor.h").read_text(encoding="utf-8")
for t in (
    '#include "125a_wav_c3_keyboard.h"',
    'portable::WavC3Keyboard wavKeyMap_;',
    'if(!wavKeyMap_.remap(mapped,size,settings_.wavC3Keyboard))return;',
    'const std::span raw(mapped.data(),size);',
    'midiTools_.resetInputState();wavKeyMap_.reset();',
):
    assert t in e,("P018 MIDI source missing "+t)
for t in (
    'bool wavC3Keyboard=false;',
    'if(s.wavC3Keyboard)o<<"wavmidic3=1\\n";',
    'else if(key=="wavmidic3"){',
    'throw std::runtime_error("Invalid WAV MIDI C3 project setting")',
):
    assert t in s,("P018 song source missing "+t)
for t in (
    'L"WAV keyboard C3 (MIDI 60 -> original EII MIDI 48, host input only)"',
    'case 61:backend_.updateSettings([](PluginSettings& x){x.wavC3Keyboard=!x.wavC3Keyboard;});break;',
    'backend_.updateSettings([](PluginSettings& x){x.wavC3Keyboard=true;});',
    'L"Studio One C3 / MIDI60 -> EII MIDI48"',
):
    assert t in v,("P018 UI source missing "+t)
a=v[v.index("case 740:{"):v.index("case 741:")]
assert a.index("auto source=std::make_shared") < a.index("x.wavC3Keyboard=true") < a.index("e.autoImportWav")
b=e[e.index("void applyMidi(const std::uint8_t* bytes,unsigned size)"):
    e.index("void applyEvent(const HostEvent& e)")]
assert b.index("if(!wavKeyMap_.remap(")<b.index("midiTools_.adapt(")<b.index("machine_->receiveMidi(")
assert "machine_->receiveMidi(std::span(packet.bytes.data(),size))" in b
assert "machine_->" not in (Path(__file__).resolve().parents[1]/"src/125a_wav_c3_keyboard.h").read_text()
print("P018 C3 keyboard host-only routing, GUI WAV selection and song state PASS")
