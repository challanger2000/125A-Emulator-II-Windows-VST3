#!/usr/bin/env python3
"""P028 default-model acceptance, including an adversarial negative control.
This is SOURCE/CONTROL QA only, NOT Windows VST3/Studio One host acceptance.
"""
import importlib.util
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p028", root/"tools/apply-p028-eii-default.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source=(root/"upstream/eii-emu/src/vst3/eii_vst3.cpp").read_text(encoding="utf-8")
state=(root/"upstream/eii-emu/src/vst3/plugin_state.h").read_text(encoding="utf-8")
assert module.NEW in source and module.OLD not in source, "new Custom instances must select EII SSM2045 M2"
assert "if(eii::vst::loadPluginDefaults(d))" in source, "explicit saved user defaults retained"
assert "void freshDefaults()" in source, "new-instance startup path absent"
assert "s.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;" in source
assert "case analog::RuntimeAudioMode::EiiiCustom" in state, "optional CEM mode must remain"
assert "i==4?analog::RuntimeAudioMode::EiiiCustom" in state
assert "i==5?analog::RuntimeAudioMode::Ssm2Chip" in state
assert 'else if(key=="model")s.audioMode=audioModeFromIndex' in state, "project recall model index not preserved"
assert module.patch(module.OLD) == module.NEW, "positive patch cannot apply"
try:
    module.patch("s.audioMode=eii::analog::RuntimeAudioMode::BasicVoice;")
except RuntimeError:
    pass
else:
    raise AssertionError("negative control failed: wrong upstream default was accepted")
try:
    module.patch(module.NEW)
except RuntimeError:
    pass
else:
    raise AssertionError("negative control failed: already-patched source accepted")
print("P028 EII SSM2045 M2 96k default / explicit user preference / project CEM recall / negative controls: SOURCE PASS")
