#!/usr/bin/env python3
"""P034 integration gate. An old host input echo or fake firmware MIDI OUT
must fail this contract; code/text checks alone do not prove musical accuracy.
"""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENG=(ROOT/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
VST=(ROOT/"upstream/eii-emu/src/vst3/eii_vst3.cpp").read_text(encoding="utf-8")
UART=(ROOT/"upstream/eii-emu/src/midi_serial.h").read_text(encoding="utf-8")
HOST=(ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp").read_text(encoding="utf-8")
PARSER=(ROOT/"upstream/eii-emu/src/125a_original_midi_out.h").read_text(encoding="utf-8")
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
patch=load("p034","tools/apply-p034-original-midi-out-vst3.py")
host=load("p034host","tools/apply-p034-midi-out-host-test.py")

for token in (
    'SpscQueue<midiout::Byte,8192> originalMidiOut_',
    'machine_->midiSerial.popTx(completed)',
    'originalMidiOut_.push(packet)',
    'if(autonomousBoot_.active()',
    '!bootGate_.load(std::memory_order_acquire)',
    'localAnchorEpoch_!=epoch||tick<anchorTickLocal_',
    'latency_.load(std::memory_order_relaxed)',
    'originalMidiParser_.reset();',
    'drainOriginalMidiOut(std::uint64_t blockStart,int blockLength',
    'if(b.frame>=end)break;',
    'originalMidiOutPreboot_',
    'originalMidiOutDrops_',
):assert token in ENG,token
for token in (
    'if(type==kEvent&&(dir==kInput||dir==kOutput))return 1;',
    'dir==kOutput?"Original MIDI Out":"MIDI In"',
    'data.outputEvents->addEvent(e)',
    'Event::kNoteOnEvent',
    'Event::kNoteOffEvent',
    'Event::kPolyPressureEvent',
    'Event::kLegacyMIDICCOutEvent',
    'engine_->drainOriginalMidiOut(midiBlockStart,n,',
    '"\\nmidioutdrops="<<engine_->originalMidiOutDrops()',
):assert token in VST,token
assert 'txCharacterTicks=1280' in UART, "must depend on original MIDI OUT hardware"
assert 'if(c>=0xf8)' in PARSER and 'if(sysEx_)' in PARSER
assert 'std::uint64_t generation=0' in PARSER or 'epoch=0,generation=0,frame=0' in PARSER
assert 'original-midi-out-bus' in HOST
assert 'P034 host incoming notes never generate fake original TX events' in HOST
assert 'P034 REAL WINDOWS ORIGINAL MIDI OUT BUS PASS' in HOST

for value,fn in ((ENG,patch.patch_engine),(VST,patch.patch_product),
                 (HOST,host.patch)):
    try:fn(value)
    except RuntimeError:pass
    else:raise AssertionError("P034 duplicated patch was incorrectly accepted")

# If someone reintroduces direct host echo, fail. MIDI OUT must originate only
# from the Machine's own original SCN2651 TX completion ring, NOT queueMidi.
assert 'queueMidi(off,pending[i].bytes.data(),pending[i].size)' in VST
assert 'machine_->midiSerial.popTx(completed)' in ENG
assert 'engine_->queueMidi(' not in ENG
print("P034 original firmware TX -> bounded stamped VST3 MIDI OUT bus source, duplicate negative guards and no-echo contract: SOURCE PASS")
