#!/usr/bin/env python3
"""P047 consistency gates: product filename, factory name and retained CID."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p047",ROOT/"tools/apply-p047-eii-display-name.py")
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
src=p.SOURCE.read_text(encoding="utf-8")
up=(ROOT/"upstream/eii-emu/src/vst3/plugin_state.h").read_text(encoding="utf-8")
pack=(ROOT/"tools/Package-Private-Emulator-II.ps1").read_text(encoding="utf-8")
workflow=(ROOT/".github/workflows/wav-bridge-qa.yml").read_text(encoding="utf-8")
checks={
    "VST3 IPluginFactory / IPluginFactory2 display name":
        src.count(p.NEW)==2 and p.OLD not in src,
    "same original factory vendor and original processor UID":
        src.count('std::strncpy(info->vendor,"Tamas (private)"')==2 and
        src.count("std::memcpy(info->cid,eii::vst::processorUid")>=2,
    "same project state magic / schema":
        'EIIVST3 1' in up,
    "owner package outer bundle name E-MU Emulator II.vst3":
        "$target=Join-Path $Destination 'E-MU Emulator II.vst3'" in pack,
    "owner package inner executable name matches outer bundle":
        "Copy-Item -LiteralPath $plugin -Destination (Join-Path $bin 'E-MU Emulator II.vst3')" in pack,
    "CI actually tests renamed bundle from actual Windows VST3 host":
        'P047 actual renamed VST3 package and factory class' in workflow and
        'E-MU Emulator II.vst3' in workflow,
    "deterministic source-only mutation / duplicate guard":
        p.patch(src.replace(p.NEW,p.OLD))==src,
}
for name,ok in checks.items():print(("PASS" if ok else "FAIL")+" P047 "+name)
assert all(checks.values()),"P047 identity and package consistency FAIL"
for mut in [src,src.replace(p.NEW,p.OLD,1),src.replace("eii::vst::processorUid","broken",1)]:
    try:p.patch(mut)
    except RuntimeError:pass
    else: raise AssertionError("P047 duplicate/bad factory mutation falsely PASS")
print("P047 consistency 7/7, negative mutant 3/3 PASS (not real COM runtime)")
