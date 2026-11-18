#!/usr/bin/env python3
"""Check Windows COM host negative/positive model/default ownership test is active."""
from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"upstream/eii-emu/tools/vst3_host_test.cpp").read_text(encoding="utf-8")
for m in (
    'std::string(argv[5])=="default-filter"',
    '"P029 real fresh VST3 instance starts with original EII SSM2045 Model 2 (96k)"',
    '"P029 CEM project closing MUST NOT overwrite new EII instance default"',
    '"P029 second fresh instance remains EII after CEM project termination"',
    '"P029 explicitly stored CEM user default is honored for fresh VST3"',
    '"P029 project recall and close preserve explicit CEM global preference byte-for-byte"',
    '"P029 removing explicit override restores original EII built-in fallback"',
    '_putenv_s("LOCALAPPDATA",isolated.string().c_str())',
    'P029 ACTUAL WINDOWS VST3 DEFAULT PASS',
):
    assert m in s,m
print("P029 Windows COM host regression positive/negative assertions: SOURCE PASS")
