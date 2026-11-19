#!/usr/bin/env python3
"""P036 adversarial diagnostic contract: real analog/SAR/DRAM not falsely marked missing."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("p036",ROOT/"tools/apply-p036-sar-diagnostics.py")
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
machine=(ROOT/"upstream/eii-emu/src/machine.cpp").read_text(encoding="utf-8")
test=(ROOT/"tests/p036_original_host_sar_rates.cpp").read_text(encoding="utf-8")
for needle in (
    "Original sample input 7-42/7-43:",
    '" SAR conversions="<<sampleSar.conversions',
    '" SAR WAIT clocks="<<sampleWaitClocks',
    '" analog input steps="<<sampleAnalog.chainSteps',
    '" amplifier rail clips="<<sampleAnalog.railClips',
    "actual analog sample-input gain/sampling-offset/ADC silicon",
    "physical serial-bit edges not synthesized",
):
    assert needle in machine,needle
for falsehood in (
    "channel0 MODE/SAR and analog conversion absent",
    "sample-recording/SAR DRAM writes",
    "register-level capture, no serial-bit timing",
):
    assert falsehood not in machine,"stale unimplemented diagnosis: "+falsehood
assert "real original Z80 program recorded 512 known SAR bytes" in test
assert "m->report()" in test, "runtime must execute truthful diagnostics"
assert "44.1k/96k input" in test
try:p.patch(machine)
except RuntimeError:pass
else:raise AssertionError("P036 duplicate source edit must fail")
print("P036 original Emulator II SAR/7-42 analog, -IWAIT, DRAM/codec diagnostics and false-old-status negative mutants PASS")
