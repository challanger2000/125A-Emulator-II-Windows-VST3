#!/usr/bin/env python3
"""P032: enable the existing real EII S3528 reconstruction model on *new*
125A Custom VST3 instances by default, without overwriting saved settings.

Source pin is a build-time submodule. Never modify or publish Tuth upstream.
"""
import argparse
import subprocess
from pathlib import Path

PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PRODUCT=UP/"src/vst3/eii_vst3.cpp"
OLD="s.nativeAudio=p.nativeAudio;s.reconstruction=p.reconstruction;s.midiWheels=p.midiWheels;"
NEW="""s.nativeAudio=p.nativeAudio;
        // 125A default: render the original EII's S3528 reconstruction stage.
        // This is the existing nominal filter, not a new silicon-calibrated model.
        // Only the first-instance fallback uses it. Saved song IBStreams and
        // explicitly saved plug-in defaults retain the user's prior selection.
        s.reconstruction=true;s.midiWheels=p.midiWheels;"""

def patch(src):
    if src.count("s.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;")!=1:
        raise RuntimeError("P032 requires P028 original EII Model 2 new-instance default")
    if src.count("if(--initialized_==0){setHandler(nullptr);engine_.reset();}")!=1:
        raise RuntimeError("P032 requires P029 global-default write protection")
    if src.count(OLD)!=1:
        raise RuntimeError(f"P032 S3528 new-instance default anchor count {src.count(OLD)}, wanted 1")
    if src.count("if(eii::vst::loadPluginDefaults(d))")!=1:
        raise RuntimeError("P032 explicit user-default preference loading must survive")
    return src.replace(OLD,NEW,1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError(f"P032 upstream pin changed: {sha}")
    original=PRODUCT.read_text(encoding="utf-8")
    edited=patch(original)
    if a.verify:
        print("P032 new-instance original EII S3528 route source preflight PASS")
    else:
        PRODUCT.write_text(edited,encoding="utf-8",newline="\n")
        print("P032 first-run Custom VST3 defaults to EII SSM2045 M2 + S3528 ON")
if __name__=="__main__":
    main()
