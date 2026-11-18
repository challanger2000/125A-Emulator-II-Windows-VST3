#!/usr/bin/env python3
"""Apply the 125A WAV-to-original-ADC input UI bridge to PINNED upstream only.
This edits an ephemeral checked-out submodule worktree, never upstream GitHub.
It must not silently apply to a future changed upstream snapshot.
"""
import argparse
from pathlib import Path
import shutil
import subprocess

UPSTREAM_SHA = "e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "eii-emu"
EDITOR = UPSTREAM / "src" / "vst3" / "plugin_editor.h"
HEADER = UPSTREAM / "src" / "125a_wav_input.h"
def replace_one(content, old, new, label):
    if content.count(old) != 1:
        raise RuntimeError(f"Unrecognized upstream {label} anchor: {content.count(old)} matches")
    return content.replace(old, new, 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Check source and patchability without mutation")
    args = parser.parse_args()
    sha = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != UPSTREAM_SHA:
        raise RuntimeError(f"Wrong upstream checkout {sha}; wanted {UPSTREAM_SHA}")
    old = EDITOR.read_text(encoding="utf-8")
    new = replace_one(
        old,
        '#include "vst3/plugin_engine.h"\n',
        '#include "vst3/plugin_engine.h"\n#include "125a_wav_input.h"\n',
        "header",
    )
    new = replace_one(
        new,
        '        AppendMenuW(menu,check(s.directImageWrites),30,L"Direct image writes (next mount / boot)");',
        '        AppendMenuW(menu,MF_STRING,70,L"125A: WAV als SAMPLE-Eingang vorbereiten...");\n'
        '        AppendMenuW(menu,MF_STRING,71,L"125A: WAV-Sample-Eingang deaktivieren");\n'
        '        AppendMenuW(menu,check(s.directImageWrites),30,L"Direct image writes (next mount / boot)");',
        "menu",
    )
    # These operations occur on the GUI/control thread. The new immutable
    # SampleInputSource is published by PluginEngine::post to the machine owner.
    command = r'''        case 70:{
            std::filesystem::path file;
            if(!openFile(file,L"WAV files (*.wav)\0*.wav\0\0",
                         L"Select WAV for the original EII SAMPLE input"))break;
            try{
                auto source=eii::wav::loadSource(file);
                e.sampleSource(std::move(source));
                ask(L"WAV prepared as analog sample input. In the original EII panel, "
                    L"use SAMPLE to record and then save the resulting bank. "
                    L"This first bridge does NOT create a playable preset automatically "
                    L"and does NOT embed the WAV in the DAW project.",
                    L"125A WAV input",MB_ICONINFORMATION);
            }catch(const std::exception& ex){
                ask(wide(ex.what()),L"125A WAV import rejected",MB_ICONERROR);
            }
            break;}
        case 71:e.sampleSource(nullptr);break;
'''
    new = replace_one(new, '        case 10:insertFloppy(false);break;',
                      command + '        case 10:insertFloppy(false);break;', "commands")
    assert new != old
    if args.verify:
        print("WAV bridge upstream SHA/anchors: PASS (no modification)")
        return
    shutil.copyfile(ROOT / "src" / "125a_wav_input.h", HEADER)
    EDITOR.write_text(new, encoding="utf-8", newline="\n")
    print("125A WAV bridge applied in local submodule worktree")

if __name__ == "__main__":
    main()
