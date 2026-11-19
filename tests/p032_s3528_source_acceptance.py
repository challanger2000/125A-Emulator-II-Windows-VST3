#!/usr/bin/env python3
"""P032 source/negative controls. Product PCM fidelity still requires a
separate original-ROM+bank, real hardware/Windows audio comparison.
"""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p032",ROOT/"tools/apply-p032-s3528-production-default.py")
p032=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p032)

source=(ROOT/"upstream/eii-emu/src/vst3/eii_vst3.cpp").read_text(encoding="utf-8")
# P045 deliberately changes the newly generated P032 nativeAudio assignment.
# Verify P032's original S3528 patch after reversing ONLY the additive P045
# first-run native-default overlay; keep the runtime product itself unchanged.
p045spec=importlib.util.spec_from_file_location("p045",ROOT/"tools/apply-p045-native-dac-default.py")
p045=importlib.util.module_from_spec(p045spec)
p045spec.loader.exec_module(p045)
assert source.count(p045.NEW)==1 and p045.OLD not in source
p032Source=source.replace(p045.NEW,p045.OLD,1)
settings=(ROOT/"upstream/eii-emu/src/vst3/plugin_state.h").read_text(encoding="utf-8")
engine=(ROOT/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
runtime=(ROOT/"upstream/eii-emu/src/nonlinear_voice.h").read_text(encoding="utf-8")
host=(ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp").read_text(encoding="utf-8")
assert p032.NEW in p032Source and p032.OLD not in p032Source
assert "s.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;" in source
assert "if(eii::vst::loadPluginDefaults(d))" in source
assert "bool saveDefaults()override{return eii::vst::savePluginDefaults(settings());}" in source
assert "s.reconstruction=p.reconstruction" not in source
assert "bool nativeAudio=false,reconstruction=false;" in settings, "do not rewrite old per-song fallback data"
assert '<<"\\ns3528="<<s.reconstruction' in settings, "host project must serialize reconstruction switch"
assert 'else if(key=="s3528")s.reconstruction=flag(v)' in settings
assert "machine_->reconstruction(settings_.reconstruction)" in engine
assert "reconstruction_.process" in runtime
assert "P032 S3528 REAL WINDOWS DEFAULT ON" in host
assert "P032 old saved CEM project retains S3528 bypass OFF" in host
assert "P032 explicit user preference S3528 bypass OFF remains honored" in host
assert "P032 removing user override restores EII original S3528 ON" in host
assert 'settings=replaceKey(settings,"s3528","1");' in host, "owner-only ROM+Choir test must actually enable S3528"
assert 'in.status("applieds3528")=="1"' in host, "owner test must check applied S3528"
assert 'saved host state lost original EII reconstruction route' in host
assert 'reopened original project state unexpectedly disabled S3528' in host
assert p032.patch(p032Source.replace(p032.NEW,p032.OLD,1))==p032Source, "positive default patch mutation"
for mutant in (
    p032Source,
    p032Source.replace("s.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;",
                   "s.audioMode=eii::analog::RuntimeAudioMode::EiiiCustom;",1),
    p032Source.replace("if(--initialized_==0){setHandler(nullptr);engine_.reset();}",
                   "if(--initialized_==0){eii::vst::savePluginDefaults(settings());setHandler(nullptr);engine_.reset();}",1),
):
    try:p032.patch(mutant)
    except RuntimeError:pass
    else:raise AssertionError("P032 negative source mutation incorrectly accepted")
print("P032 existing SSM2045 M2 + nominal S3528 new-instance route, legacy-state preservation and Windows COM negative controls: SOURCE PASS")
