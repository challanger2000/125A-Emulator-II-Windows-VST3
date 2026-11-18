#!/usr/bin/env python3
"""P029: protect the user's explicit new-instance EII default from unrelated project closes.

The original Custom VST3 automatically copied project settings to the global
defaults file on termination and every editor update. That silently changed the
model used by the NEXT instance. Keep the explicit Save defaults menu action.
"""
import argparse
import subprocess
from pathlib import Path

PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENGINE=UP/"src/vst3/eii_vst3.cpp"
STATE=UP/"src/vst3/plugin_state.h"

def one(s,old,new,label):
    count=s.count(old)
    if count!=1:
        raise RuntimeError(f"P029 {label}: expected exactly one source anchor; got {count}")
    return s.replace(old,new,1)

def patch_engine(s):
    s=one(s,
        "if(--initialized_==0){if(engine_)eii::vst::savePluginDefaults(settings());setHandler(nullptr);engine_.reset();}",
        "if(--initialized_==0){setHandler(nullptr);engine_.reset();}",
        "no accidental global defaults when closing an old host project")
    s=one(s,
        "        eii::vst::savePluginDefaults(settings()); // what was ticked is what the next instance gets\n",
        "        // Persist global defaults only after explicit Settings > Save as default.\n",
        "no accidental global defaults during an ordinary UI setting change")
    if s.count("bool saveDefaults()override{return eii::vst::savePluginDefaults(settings());}")!=1:
        raise RuntimeError("P029 explicit Save settings as default action is missing")
    if s.count("eii::vst::savePluginDefaults(settings())")!=1:
        raise RuntimeError("P029 unexpected implicit global-default writers remain")
    return s

def patch_state(s):
    return one(s,
        "// everything). Written on every settings change and when the plug-in closes.",
        "// everything). Written only by the explicit Save as default menu action.",
        "new-instance saved-default ownership documentation")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    args=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError(f"P029 source pin mismatch: {sha}")
    before=ENGINE.read_text(encoding="utf-8")
    state=STATE.read_text(encoding="utf-8")
    if "s.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;" not in before:
        raise RuntimeError("P029 requires P028 EII SSM2045 default applied first")
    new=patch_engine(before)
    new_state=patch_state(state)
    if args.verify:
        print("P029 pinned actual VST3 implicit-default writers / explicit command: source preflight PASS")
    else:
        ENGINE.write_text(new,encoding="utf-8",newline="\n")
        STATE.write_text(new_state,encoding="utf-8",newline="\n")
        print("P029 removed implicit global-default writes; explicit save still works")

if __name__=="__main__":
    main()
