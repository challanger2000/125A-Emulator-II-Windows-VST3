#!/usr/bin/env python3
"""Apply 125A P003 firmware WAV importer AFTER apply-wav-bridge.py.
Both edits are source-pinned, local build overlays; upstream GitHub is untouched.
"""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "upstream/eii-emu"
ENGINE = UP / "src/vst3/plugin_engine.h"
EDITOR = UP / "src/vst3/plugin_editor.h"
EXPECTED = "e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def replace_once(src, before, after, label):
    n = src.count(before)
    if n != 1:
        raise RuntimeError(f"P003 {label}: expected exactly one original anchor, found {n}")
    return src.replace(before, after, 1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=EXPECTED:
        raise RuntimeError(f"Unsupported upstream commit {sha}")
    e=ENGINE.read_text(encoding="utf-8")
    v=EDITOR.read_text(encoding="utf-8")
    if "autoImportWav(" in e or "wavCapture_" in e:
        raise RuntimeError("Already patched or upstream integration conflict")
    # The first source-pinned overlay must have provided the old P001 menu.
    e=replace_once(e, '#include "vst3/host_sample_input.h"',
       '#include "vst3/host_sample_input.h"\n#include "125a_wav_input.h"\n#include "125a_firmware_capture.h"\n#include <optional>',
       "engine includes")
    e=replace_once(e, '    int recallProgram=-1;bool recallPending=false;',
       '    int recallProgram=-1;bool recallPending=false;\n'
       '    std::string wavStatus;bool wavActive=false,wavSuccess=false;std::uint64_t wavReport=0;',
       "status fields")
    e=replace_once(e,
       '    void sampleSource(std::shared_ptr<analog::SampleInputSource> s){post([this,s]{sampleSource_=s;if(machine_)machine_->sampleInput=s?s:hostInput_;});}',
       r'''    void sampleSource(std::shared_ptr<analog::SampleInputSource> s){
        post([this,s]{if(wavCapture_.active())return;sampleSource_=s;
            if(machine_)machine_->sampleInput=s?s:hostInput_;});
    }
    // UI file decoding is complete before this command. Work is conducted
    // only on the owner, through original firmware's physical scanner contacts.
    void autoImportWav(std::shared_ptr<wav::Source> source){
        post([this,source]{
            if(wavCapture_.active()){error_="125A WAV import already running.";return;}
            if(!producing()||!machine_||!floppyState().mounted){
                error_="125A WAV requires booted EII with OS 3.1 floppy mounted.";return;
            }
            if(!source||source->durationTicks()==0||
               source->durationTicks()>wav::FirmwareCapture::maxDuration){
                error_="125A WAV: current first-stage limit is 10 seconds.";return;
            }
            const auto lcd=machine_->lcd.line(0);
            if(lcd.size()<3||lcd[0]!='P'||lcd[1]<'0'||lcd[1]>'9'||lcd[2]<'0'||lcd[2]>'9'){
                error_="Return to the EII Pxx preset screen before WAV import.";return;
            }
            error_.clear();
            oldSampleSource_=sampleSource_;autoWavSource_=source;
            sampleSource_=source;machine_->sampleInput=source;
            auto first=wavCapture_.begin(machine_->ticks,source->durationTicks());
            if(first.completed){wavError(first.error);return;}
            wavAction(first.action);wavStatus_=wavCapture_.stageName();
        });
    }
    void cancelAutoWav(){
        post([this]{if(wavCapture_.active())
            wavError("WAV cancelled; emulated sample RAM may already have changed.");});
    }''', "public sampleSource and auto WAV commands")
    e=replace_once(e,
       '    std::shared_ptr<analog::SampleInputSource> sampleSource_;',
       r'''    std::shared_ptr<analog::SampleInputSource> sampleSource_,oldSampleSource_;
    std::shared_ptr<wav::Source> autoWavSource_;
    wav::FirmwareCapture wavCapture_;
    std::optional<ScannerButton> wavHeld_;
    std::string wavStatus_="Idle";
    std::uint64_t wavReport_=0;bool wavSuccess_=false;''', "owner WAV state")
    e=replace_once(e,
       '    static ScannerAnalogInput input(unsigned n)',
       r'''    void wavRelease(){
        if(wavHeld_){contact(unsigned(*wavHeld_),false);wavHeld_.reset();}
        if(autoWavSource_)autoWavSource_->disarmReadGate();
        sampleSource_=oldSampleSource_;
        if(machine_)machine_->sampleInput=sampleSource_?sampleSource_:hostInput_;
        autoWavSource_.reset();oldSampleSource_.reset();wavCapture_.reset();
    }
    void wavError(const char* message){
        wavStatus_=message?message:"Unknown firmware WAV error";
        error_="125A WAV failed: "+wavStatus_;
        wavSuccess_=false;++wavReport_;wavRelease();
    }
    void wavAction(wav::CaptureAction a){
        if(!machine_)return;
        using A=wav::CaptureAction;
        ScannerButton b=ScannerButton::Sample;bool down=false;
        switch(a){
        case A::SampleDown:b=ScannerButton::Sample;down=true;break;
        case A::SampleUp:b=ScannerButton::Sample;break;
        case A::ArmForceDown:
            if(autoWavSource_)autoWavSource_->armAfterRead(&machine_->sampleReads,machine_->sampleReads);
            b=ScannerButton::Digit9;down=true;break;
        case A::ForceUp:b=ScannerButton::Digit9;break;
        case A::StopDown:b=ScannerButton::Digit0;down=true;break;
        case A::StopUp:b=ScannerButton::Digit0;break;
        default:return;
        }
        contact(unsigned(b),down);
        if(down)wavHeld_=b;else wavHeld_.reset();
    }
    void wavStep(){
        if(!wavCapture_.active()||!machine_||!autoWavSource_)return;
        const auto mode=machine_->channel0Mode();
        const auto action=wavCapture_.advance(machine_->ticks,machine_->lcd.line(0),
            machine_->lcd.line(1),machine_->sampleReads,autoWavSource_->started(),
            autoWavSource_->startTick(),mode.known&&mode.high);
        wavAction(action.action);
        if(action.completed){
            if(action.success){
                wavStatus_="Emulator-II firmware accepted WAV (Sample is good) and returned to Pxx. "
                           "The voice lives in volatile sampler RAM, root MIDI 48. "
                           "DAW save/reopen is NOT supported by this milestone.";
                wavSuccess_=true;++wavReport_;wavRelease();
            }else wavError(action.error);
        }else wavStatus_=wavCapture_.stageName();
    }
    static ScannerAnalogInput input(unsigned n)''',
       "owner firmware driver")
    e=replace_once(e,'    void bootNow(bool discard,bool fromState){',
       '    void bootNow(bool discard,bool fromState){\n'
       '        if(wavCapture_.active())wavError("Boot interrupted WAV capture; RAM may have changed.");',
       "boot lifecycle")
    e=replace_once(e,'                machine_->run(n);',
       '                machine_->run(n);\n                wavStep();',
       "machine run hook")
    e=replace_once(e,
       '        s.recallProgram=recallProgram_.load();s.recallPending=recallPending_;',
       '        s.recallProgram=recallProgram_.load();s.recallPending=recallPending_;\n'
       '        s.wavStatus=wavStatus_;s.wavActive=wavCapture_.active();'
       's.wavSuccess=wavSuccess_;s.wavReport=wavReport_;',
       "status publication")

    v=replace_once(v,
       'AppendMenuW(menu,MF_STRING,740,L"125A: WAV als SAMPLE-Eingang vorbereiten...");',
       'AppendMenuW(menu,MF_STRING,740,L"125A: WAV automatisch aufnehmen...");',
       "menu start")
    v=replace_once(v,
       'AppendMenuW(menu,MF_STRING,741,L"125A: WAV-Sample-Eingang deaktivieren");',
       'AppendMenuW(menu,MF_STRING,741,L"125A: Aufnahme abbrechen");',
       "menu cancel")
    start='                auto source=eii::wav::loadSource(file);'
    end='            }catch(const std::exception& ex){'
    i=v.find(start);j=v.find(end,i)
    if i<0 or j<0 or v.find(start,i+1)>=0:
        raise RuntimeError("P001 WAV picker anchor missing/nonunique")
    v=v[:i]+'''                auto source=std::make_shared<eii::wav::Source>(eii::wav::load(file));
                e.autoImportWav(std::move(source));
'''+v[j:]
    v=replace_once(v,'        case 741:e.sampleSource(nullptr);break;',
       '        case 741:e.cancelAutoWav();break;', "cancel UI")
    v=replace_once(v,
       '    HFONT font_=nullptr;std::uint64_t shownRevision_=0;std::string lastError_;bool modal_=false;',
       '    HFONT font_=nullptr;std::uint64_t shownRevision_=0;std::string lastError_;'
       'std::uint64_t lastWavNotice_=0;bool modal_=false;',
       "editor notification guard")
    v=replace_once(v,'        if(s.panel.error.empty())lastError_.clear();',
       '''        if(s.panel.error.empty())lastError_.clear();
        if(!modal_&&s.wavReport!=lastWavNotice_){
            lastWavNotice_=s.wavReport;
            if(s.wavReport&&s.wavSuccess)
                ask(wide(s.wavStatus),L"125A Emulator II WAV",MB_ICONINFORMATION);
        }''', "editor completion status")
    v=replace_once(v,'        if(!s.panel.error.empty())o<<L"\\n\\nLast message: "<<wide(s.panel.error);',
       '        o<<L"\\n125A WAV: "<<wide(s.wavStatus);\n'
       '        if(!s.panel.error.empty())o<<L"\\n\\nLast message: "<<wide(s.panel.error);',
       "status dialog")
    if args.verify:
        print("P003 WAV original firmware GUI/worker patch: anchors PASS")
        return
    shutil.copyfile(ROOT/"src/125a_wav_input.h",UP/"src/125a_wav_input.h")
    shutil.copyfile(ROOT/"src/125a_firmware_capture.h",UP/"src/125a_firmware_capture.h")
    ENGINE.write_text(e,encoding="utf-8",newline="\n")
    EDITOR.write_text(v,encoding="utf-8",newline="\n")
    print("P003 applied to local source-pinned EII VST3, original upstream untouched")

if __name__=="__main__":
    main()
