#!/usr/bin/env python3
"""P011 source/guard acceptance. Firmware and host audio must be tested separately."""
from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
def need(v):
    if v not in s:raise AssertionError("Missing P011 integration: "+v)
for v in (
    '#include "125a_firmware_cancel.h"',
    "void beginWavCancel(std::string reason)",
    "void cancelWavAction(wav::CancelAction a)",
    "void cancelWavStep()",
    "wavCancel_.advance(machine_->ticks,mode.known,mode.high",
    'if(bankSave_.active()){',
    'Cancellation deferred: original DISK7 SAVE BANK must finish safely',
    "if(wavCapture_.active()||bankSave_.active()||wavCancel_.active())",
    "wavCapture_.reset();\n        wavCancelReason_=std::move(reason);",
    "autoWavSource_->disarmReadGate();",
    "projectBusy_.store(false,std::memory_order_release);",
    "restoreWavOriginalFloppy();",
    "beginWavCancel(action.error?",
):
    need(v)
assert s.index("wavStep();\n                cancelWavStep();\n                bankStep();")>=0
b=s[s.index("void cancelAutoWav()"):s.index("    // UI file decoding is complete",s.index("void cancelAutoWav()"))] if False else s[s.index("void cancelAutoWav()"):s.index("    void ",s.index("void cancelAutoWav()")+5)]
assert "bankError(" not in b, "Cancel must not terminate an active DISK7 write"
assert "beginWavCancel" in b
assert "wavError(" not in b, "Cancel must not immediately abandon original firmware"
print("P011 firmware cancel / protected bank-write source guards PASS")
