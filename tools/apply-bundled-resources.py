#!/usr/bin/env python3
"""Install the EIII-style VST3 Contents/Resources/ROM,OS loader (P006).
Run only AFTER original P001, P003 and P004 source-pinned overlays.
Do not commit original ROMs, OS disks, user media or firmware to GitHub.
"""
import argparse
import subprocess
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
CPP=UP/"src/vst3/eii_vst3.cpp"
DEST=UP/"src/125a_bundle_resources.h"
def replace(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"P006 {label}: expected one source anchor, found {n}")
    return s.replace(old,new,1)
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError(f"Unsupported original EII core revision {sha}")
    source=CPP.read_text(encoding="utf-8")
    if "eii::vst::resources::adopt(" in source:
        raise RuntimeError("P006 is already applied; do not patch twice")
    source=replace(source,
        '#include "vst3/plugin_editor.h"',
        '#include "vst3/plugin_editor.h"\n#include "125a_bundle_resources.h"',
        "module resource helper")
    source=replace(source,
        '''        {eii::vst::PluginSettings d;if(eii::vst::loadPluginDefaults(d)){
            d.directImageWrites=false;''',
        '''        {eii::vst::PluginSettings d;if(eii::vst::loadPluginDefaults(d)){
            eii::vst::resources::adopt(d);
            d.directImageWrites=false;''',
        "new instance with previous preference")
    source=replace(source,
        '''        std::lock_guard l(settingsMutex_);settings_=s;
    }
    std::unique_ptr<eii::vst::PluginEngine> engine_;''',
        '''        eii::vst::resources::adopt(s);
        std::lock_guard l(settingsMutex_);settings_=s;
    }
    std::unique_ptr<eii::vst::PluginEngine> engine_;''',
        "new instance first-run")
    source=replace(source,
        '            s=eii::vst::parseSettings(project.settings);',
        '''            s=eii::vst::parseSettings(project.settings);
            eii::vst::resources::adopt(s);''',
        "saved project on moved installation")
    if args.verify:
        print("P006 source-pinned Resources ROM/OS patch anchors: PASS")
        return
    shutil.copyfile(ROOT/"src/125a_bundle_resources.h",DEST)
    CPP.write_text(source,encoding="utf-8",newline="\n")
    print("P006 bundled private firmware autodiscovery installed in local VST3")
if __name__=="__main__":main()
