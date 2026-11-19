#!/usr/bin/env python3
"""P033: verify native original Z80 OUT4 -> real SCN2651, no fake host MIDI OUT."""
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
UART=(ROOT/"upstream/eii-emu/src/midi_serial.h").read_text(encoding="utf-8")
MACHINE=(ROOT/"upstream/eii-emu/src/machine.cpp").read_text(encoding="utf-8")
p=ROOT/"tools/apply-p033-original-midi-transmitter.py"
spec=importlib.util.spec_from_file_location("p033",p)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for token in (
    'static constexpr std::uint64_t txCharacterTicks=1280;',
    'static constexpr unsigned txCapacity=512;',
    'std::uint64_t txCompleted=0,txRejected=0,txDropped=0;',
    'bool writeTxData(std::uint8_t byte,std::uint64_t now)',
    'void advanceTx(std::uint64_t now)',
    'bool popTx(TxFrame& out)',
    '(txReady()?1:0)',
    '(txEmpty()?4:0)',
):
    assert token in UART,token
for token in (
    'midiSerial.writeTxData(v,ticks);',
    'if(midiSerial.txBusy())midiSerial.advanceTx(ticks);',
    'SCN2651 original MIDI TX complete=',
    'if(serialTx.size()<65536)serialTx+=char(v);',
    'if(p==6)midiSerial.writeMode(v);',
    'if(p==7)midiSerial.writeCommand(v);',
):
    assert token in MACHINE,token
assert "host MIDI OUT routing not yet implemented" in MACHINE
for src,fn in ((UART,mod.patch_uart),(MACHINE,mod.patch_machine)):
    try:fn(src)
    except RuntimeError:pass
    else:raise AssertionError("existing installed P033 overlay accepted a second time")
print("P033 original CPU OUT4 SCN2651 timed MIDI TX, bounded completed packets, negative anchors: SOURCE PASS")
