#!/usr/bin/env python3
"""P045 source & adversarial mutation gates. Not a substitute for real ROM audio."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def get(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
p045=get("tools/apply-p045-native-dac-default.py","p045")
hostPatch=get("tools/apply-p045-native-windows-host-test.py","p045host")

s=p045.PRODUCT.read_text(encoding="utf-8")
h=hostPatch.HOST.read_text(encoding="utf-8")
state=(ROOT/"upstream/eii-emu/src/vst3/plugin_state.h").read_text(encoding="utf-8")
p044=(ROOT/"tests/p040_windows_original_adversarial.h").read_text(encoding="utf-8")
tests={
    "native DAC actual fallback installed":p045.NEW in s and p045.OLD not in s,
    "SSM2045 Model2 and S3528 still first-run defaults":
        's.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;' in s
        and 's.reconstruction=true;' in s,
    "explicit standalone registry native OFF honored":
        'RegQueryValueExW(' in p045.NEW
        and 'L"NativeDacDeglitch"' in p045.NEW
        and '? (value!=0) : true' in p045.NEW,
    "no registry absent interpreted as explicit OFF":
        "if(opened!=ERROR_SUCCESS)return true;" in p045.NEW,
    "native registry query type/size verified and handle closed":
        "type==REG_DWORD" in p045.NEW and "bytes==sizeof(value)" in p045.NEW
        and "RegCloseKey(key);" in p045.NEW,
    "existing VST3 global and host saved projects authoritative":
        'if(eii::vst::loadPluginDefaults(d))' in s
        and 'bool nativeAudio=false,reconstruction=false;' in state
        and '<<"\\nnative="<<s.nativeAudio' in state,
    "existing P041 legacy route remains explicitly OFF":
        'bool native=false;' in p044
        and 'state=replaceKey(state,"native",tc.native?"1":"0");' in p044,
    "P044 native=ON original-ROM acceptance remains independent":
        'in.status("appliednative")=="1"' in p044,
    "real Windows VST3 factory asserts native ON":
        'P045 ACTUAL WINDOWS VST3 NATIVE DAC DEFAULT ON' in h,
    "historical saved project explicitly stays native OFF":
        'P045 old saved project retains explicit native DAC bypass OFF' in h,
    "new EII still native ON after historic song closes":
        'P045 new EII still has native DAC ON after closing historical native=OFF project' in h,
    "explicit global user native OFF preserved":
        'P045 explicit saved user preference native OFF remains honored' in h,
    "removing user native OFF restores hardware native ON":
        'P045 removing explicit saved native=0 preference restores EII native=1' in h,
    "original patch reproduction":
        p045.patch(s.replace(p045.NEW,p045.OLD,1))==s,
}
for key,ok in tests.items():
    print(("PASS" if ok else "FAIL")+" P045 "+key)
assert all(tests.values()),"P045 SOURCE GATE FAILURE"
for mutant in (
    s,
    s.replace('s.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;',
              's.audioMode=eii::analog::RuntimeAudioMode::EiiiCustom;',1),
    s.replace('if(eii::vst::loadPluginDefaults(d))',
              'if(false)',1),
):
    try:p045.patch(mutant)
    except RuntimeError:pass
    else:raise AssertionError("P045 source mutation incorrectly accepted")
for mutant in (
    h,
    h.replace('P032 S3528 REAL WINDOWS DEFAULT','BROKEN',1),
):
    try:hostPatch.patch(mutant)
    except RuntimeError:pass
    else:raise AssertionError("P045 host test mutation incorrectly accepted")
print("P045 SOURCE 14/14 + 5 mutation preconditions PASS; real Windows COM acceptance required")
