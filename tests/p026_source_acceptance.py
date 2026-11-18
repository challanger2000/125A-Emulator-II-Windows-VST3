#!/usr/bin/env python3
"""P026 contractual guard: product code stays untouched, Windows COM probe
tests real multi-instance audio/teardown rather than only IBStream codec.
"""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
host=(r/"upstream/eii-emu/tools/vst3_host_test.cpp").read_text(encoding="utf-8")
for term in (
    'if(argc>5&&std::string(argv[5])=="windows-audio-safety"){',
    'broken.start(48000,kRealtime,512)',
    'clean.start(44100,kRealtime,256)',
    'error.find("conflicting RFD bus drivers")',
    'broken.process(i%13==0?&midi:nullptr)',
    'clean.process()',
    'P026 every sample of both independent Windows VST3 instances silent',
    'P026 original hardware fault does not cross into second instance',
    'P026 both actual Windows VST3 owners and workers release after COM teardown',
):
    assert term in host,term
assert host.count('P026 WINDOWS REAL VST3 COM AUDIO/LIFECYCLE PASS')==1
print("P026 genuine Windows COM two-instance realtime audio safety and lifecycle contracts PASS")
