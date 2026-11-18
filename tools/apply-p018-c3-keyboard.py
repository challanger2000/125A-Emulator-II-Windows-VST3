#!/usr/bin/env python3
"""P018: Studio One MIDI 60 (C3) maps to original EII MIDI 48 after WAV import.

This is explicitly a HOST-keyboard note remap. It does not pretend to change
the original E-mu OS sample-root frequency or its bank format. The C3 option
is enabled by successful GUI WAV selection, and saved in each VST3 song.
Other EII banks can use their original octave with the Settings checkbox.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENG=UP/"src/vst3/plugin_engine.h"
STATE=UP/"src/vst3/plugin_state.h"
EDITOR=UP/"src/vst3/plugin_editor.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,old,new,name):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"P018 {name}: expected 1 anchor, found {n}")
    return s.replace(old,new,1)

def patch(e,s,v):
    for required in ("ProjectSaveFrame projectSaveFrame()const",
                     "void observeMediaReads()", "captureHddForProject()",
                     "restoreProjectMedia(", "wavAutoOsMounted_"):
        if required not in e:raise RuntimeError("P018 requires full P017 EII integration: "+required)
    if "wavC3Keyboard" in s:raise RuntimeError("P018 already installed")

    e=one(e,
        '#include "125a_portable_hdd.h"',
        '#include "125a_portable_hdd.h"\n#include "125a_wav_c3_keyboard.h"',
        "owner MIDI host adapter include")
    e=one(e,
        '    portable::LiveMediaWatch bankMediaWatch_;',
        '    portable::LiveMediaWatch bankMediaWatch_;\n'
        '    portable::WavC3Keyboard wavKeyMap_; // owner-only note pairing',
        "per-instance original MIDI note tracker")
    e=one(e,
        '''        if(!machine_)return;
        const std::span raw(bytes,size);
        const auto packet=midiTools_.adapt(raw);''',
        '''        if(!machine_)return;
        std::array<std::uint8_t,3> mapped{};
        for(unsigned i=0;i<size;++i)mapped[i]=bytes[i];
        if(!wavKeyMap_.remap(mapped,size,settings_.wavC3Keyboard))return;
        const std::span raw(mapped.data(),size);
        const auto packet=midiTools_.adapt(raw);''',
        "map NoteOn/NoteOff only before unchanged original SCN2651 serial wire")
    e=one(e,
        '''            midiTools_.resetInputState();midiTools_.wheelBridge=c.midiWheels;''',
        '''            midiTools_.resetInputState();wavKeyMap_.reset();
            midiTools_.wheelBridge=c.midiWheels;''',
        "reset held note mapping on original machine reboot")

    s=one(s,
        '    bool midiWheels=false,noteOffZero=false;',
        '''    bool midiWheels=false,noteOffZero=false;
    bool wavC3Keyboard=false; // host MIDI60 -> original EII MIDI48; per song''',
        "per-project opt-in keyboard map")
    s=one(s,
        '    o<<"levelmodel=2\\n"; // common level model (level_model.h); absent = older state, migrated on load',
        '''    if(s.wavC3Keyboard)o<<"wavmidic3=1\\n"; // optional: legacy state stays byte-identical
    o<<"levelmodel=2\\n"; // common level model (level_model.h); absent = older state, migrated on load''',
        "encode C3 setting in existing host project settings")
    s=one(s,
        '''        else if(key=="wheels")s.midiWheels=flag(v);''',
        '''        else if(key=="wavmidic3"){
            if(v!="0"&&v!="1")throw std::runtime_error("Invalid WAV MIDI C3 project setting");
            s.wavC3Keyboard=v=="1";
        }
        else if(key=="wheels")s.midiWheels=flag(v);''',
        "strictly decode C3 song setting")

    v=one(v,
        '''        AppendMenuW(menu,check(s.noteOffZero),51,L"Note Off as 90/0");''',
        '''        AppendMenuW(menu,check(s.noteOffZero),51,L"Note Off as 90/0");
        AppendMenuW(menu,check(s.wavC3Keyboard),61,
            L"WAV keyboard C3 (MIDI 60 -> original EII MIDI 48, host input only)");''',
        "visible explicit octave switch in Settings")
    v=one(v,
        '''        case 52:backend_.updateSettings([&](PluginSettings& x){x.autoBoot=!s.autoBoot;});break;''',
        '''        case 61:backend_.updateSettings([](PluginSettings& x){x.wavC3Keyboard=!x.wavC3Keyboard;});break;
        case 52:backend_.updateSettings([&](PluginSettings& x){x.autoBoot=!s.autoBoot;});break;''',
        "Settings C3 octave can be manually toggled")
    v=one(v,
        '''                auto source=std::make_shared<eii::wav::Source>(eii::wav::load(file));
                e.autoImportWav(std::move(source));''',
        '''                auto source=std::make_shared<eii::wav::Source>(eii::wav::load(file));
                // The original firmware captures at its original MIDI 48
                // position. Only the HOST's incoming keyboard is translated:
                // Studio One C3/MIDI60 sends original EII MIDI48 after import.
                // This also marks the song dirty before the queued capture.
                backend_.updateSettings([](PluginSettings& x){x.wavC3Keyboard=true;});
                e.autoImportWav(std::move(source));''',
        "automatic C3 keyboard selection for GUI WAV import")
    v=one(v,
        '''        if(!s.panel.error.empty())o<<L"\\n\\nLast message: "<<wide(s.panel.error);''',
        '''        o<<L"\\nWAV MIDI keyboard: "<<
            (backend_.settings().wavC3Keyboard?
                L"Studio One C3 / MIDI60 -> EII MIDI48":
                L"Original EII MIDI note numbering (unshifted)");
        if(!s.panel.error.empty())o<<L"\\n\\nLast message: "<<wide(s.panel.error);''',
        "status shows the actual host octave mapping")
    return e,s,v

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P018 original EII core SHA mismatch")
    out=patch(ENG.read_text(encoding="utf-8"),
              STATE.read_text(encoding="utf-8"),
              EDITOR.read_text(encoding="utf-8"))
    if args.verify:
        print("P018 original EII C3 host keyboard mapping source anchors: PASS")
        return
    shutil.copyfile(ROOT/"src/125a_wav_c3_keyboard.h",UP/"src/125a_wav_c3_keyboard.h")
    for path,s in zip((ENG,STATE,EDITOR),out):
        path.write_text(s,encoding="utf-8",newline="\n")
    print("P018 safe host MIDI60 -> original EII MIDI48 mapper installed")

if __name__=="__main__":main()
