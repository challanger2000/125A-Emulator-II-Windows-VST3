#!/usr/bin/env python3
"""P029 source-only guards, not substitute for the real Windows COM host test."""
import importlib.util
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p029",root/"tools/apply-p029-default-safety.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
engine=(root/"upstream/eii-emu/src/vst3/eii_vst3.cpp").read_text(encoding="utf-8")
state=(root/"upstream/eii-emu/src/vst3/plugin_state.h").read_text(encoding="utf-8")
assert "s.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;" in engine
assert "if(--initialized_==0){setHandler(nullptr);engine_.reset();}" in engine
assert "Persist global defaults only after explicit Settings > Save as default." in engine
assert engine.count("eii::vst::savePluginDefaults(settings())")==1
assert "bool saveDefaults()override{return eii::vst::savePluginDefaults(settings());}" in engine
assert "Written only by the explicit Save as default menu action." in state
old_terminate="if(--initialized_==0){if(engine_)eii::vst::savePluginDefaults(settings());setHandler(nullptr);engine_.reset();}"
old_update="        eii::vst::savePluginDefaults(settings()); // what was ticked is what the next instance gets\n"
mutant=engine.replace(
    "if(--initialized_==0){setHandler(nullptr);engine_.reset();}",
    old_terminate,1).replace(
    "        // Persist global defaults only after explicit Settings > Save as default.\n",
    old_update,1)
assert mutant!=engine
assert p.patch_engine(mutant)==engine, "old implicit overwrite must be detected and corrected"
try:p.patch_engine(engine)
except RuntimeError:pass
else:raise AssertionError("already-patched source accepted; negative control invalid")
print("P029 source writer ownership + pre-fix negative / explicit global Save path: PASS")
