#!/usr/bin/env python3
"""P045: native hardware DAC/Deglitch is the EII default, not the shortcut.

Apply AFTER P028 (SSM2045 model 2), P029 (safe user defaults) and P032
(S3528 on); preserve existing VST3 song and explicitly saved user defaults.
The original Tuth source stays pinned and unchanged in GitHub.
"""
import argparse
import subprocess
from pathlib import Path

PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PRODUCT=UP/"src/vst3/eii_vst3.cpp"
OLD="s.nativeAudio=p.nativeAudio;"
NEW=r"""s.nativeAudio=[&](){
            // Native AM6072 + 13202/TL084 is the actual EII default.
            // Distinguish an old missing standalone registry value (fallback)
            // from an explicit user-selected OFF. Never rewrite this preference.
            HKEY key=nullptr;
            const LONG opened=RegOpenKeyExW(
                HKEY_CURRENT_USER,
                L"Software\\Tuth\\EIIEmulator\\FrontPanel",
                0,KEY_QUERY_VALUE,&key);
            if(opened!=ERROR_SUCCESS)return true;
            DWORD value=0,type=0,bytes=sizeof(value);
            const LONG found=RegQueryValueExW(
                key,L"NativeDacDeglitch",nullptr,&type,
                reinterpret_cast<BYTE*>(&value),&bytes);
            RegCloseKey(key);
            return found==ERROR_SUCCESS && type==REG_DWORD
                && bytes==sizeof(value) ? (value!=0) : true;
        }();"""

def patch(src):
    for required in (
        's.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;',
        's.reconstruction=true;s.midiWheels=p.midiWheels;',
        'if(eii::vst::loadPluginDefaults(d))',
        'if(--initialized_==0){setHandler(nullptr);engine_.reset();}',
    ):
        if src.count(required)!=1:
            raise RuntimeError(f"P045 prerequisite missing/ambiguous: {required!r}: {src.count(required)}")
    if src.count(OLD)!=1:
        raise RuntimeError(f"P045 native fallback anchor {src.count(OLD)}, wanted 1")
    return src.replace(OLD,NEW,1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P045 pinned upstream changed: "+sha)
    current=PRODUCT.read_text(encoding="utf-8")
    updated=patch(current)
    if a.verify:
        print("P045 native DAC new-instance default, registry absence distinction and original project/defaults: PATCH PREFLIGHT PASS")
    else:
        PRODUCT.write_text(updated,encoding="utf-8",newline="\n")
        print("P045 new EII instance: SSM2045 Model2 + switched native DAC ON + S3528 ON; saved user preferences retained")
if __name__=="__main__":
    main()
