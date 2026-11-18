#!/usr/bin/env python3
"""P011 source-anchored original firmware CANCEL: STOP -> SAMPLE -> Pxx -> disk restore.
Applies only after P010, P008, P004 overlays. Never interrupts firmware DISK7 writes.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENGINE=UP/"src/vst3/plugin_engine.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"P011 {label}: expected exactly one source anchor, found {n}")
    return s.replace(old,new,1)

def patch(s):
    if "cancelWavStep()" in s:raise RuntimeError("P011 already applied")
    for required in ("cloneSelectedBank","wavAutoOsMounted_","bankSave_.active()","restoreWavOriginalFloppy()"):
        if required not in s:raise RuntimeError(f"P011 requires P010/P008 overlay: {required}")
    s=one(s,
        '#include "125a_selected_bank.h"',
        '#include "125a_selected_bank.h"\n#include "125a_firmware_cancel.h"',
        "include cancel FSM")
    s=one(s,
        '    wav::FirmwareCapture wavCapture_;',
        '    wav::FirmwareCapture wavCapture_;\n    wav::FirmwareCancel wavCancel_;\n    std::string wavCancelReason_;',
        "owner cancel state")
    s=one(s,
        '''    void cancelAutoWav(){
        post([this]{
            if(wavCapture_.active())wavError("WAV cancelled; volatile sample RAM may have changed.");
            if(bankSave_.active())bankError("Bank save cancelled; old project bank retained.");
        });
    }''',
        '''    void cancelAutoWav(){
        post([this]{
            if(wavCapture_.active()){
                beginWavCancel("WAV cancelled by user; previous committed bank retained.");
                return;
            }
            if(bankSave_.active()){
                // The original EII is already writing DISK7. Never corrupt a
                // bank by stopping the floppy mid-track: finish and commit.
                wavStatus_="Cancellation deferred: original DISK7 SAVE BANK must finish safely.";
                ++wavReport_;
            }
        });
    }''',
        "firmware-safe public cancellation")
    s=one(s,
        '''            if(wavCapture_.active()||bankSave_.active()){error_="125A WAV import or bank save already running.";return;}''',
        '''            if(wavCapture_.active()||bankSave_.active()||wavCancel_.active()){
                error_="125A WAV import, bank save, or firmware cancellation already running.";return;
            }''',
        "prevent restart during firmware recovery")
    s=one(s,
        '''        autoWavSource_.reset();oldSampleSource_.reset();wavCapture_.reset();''',
        '''        autoWavSource_.reset();oldSampleSource_.reset();wavCapture_.reset();wavCancel_.reset();
        wavCancelReason_.clear();''',
        "release cancel state only after recovery")
    s=one(s,
        '''    void wavStep(){
        if(!wavCapture_.active()||!machine_||!autoWavSource_)return;''',
        '''    void beginWavCancel(std::string reason){
        if(!machine_){wavError(reason.c_str());return;}
        if(wavCancel_.active())return;
        // Keep the source bound but disarm all SAR reads before issuing
        // original panel STOP/EXIT. Do not hot-swap the original floppy.
        if(wavHeld_){contact(unsigned(*wavHeld_),false);wavHeld_.reset();}
        if(autoWavSource_)autoWavSource_->disarmReadGate();
        wavCapture_.reset();
        wavCancelReason_=std::move(reason);
        wavCancel_.begin(machine_->ticks);
        wavStatus_=wavCancel_.label();
        wavSuccess_=false;
    }
    void cancelWavAction(wav::CancelAction a){
        if(!machine_||a==wav::CancelAction::None)return;
        const bool stop=a==wav::CancelAction::StopDown||a==wav::CancelAction::StopUp;
        const bool pressed=a==wav::CancelAction::StopDown||a==wav::CancelAction::SampleDown;
        const auto key=stop?ScannerButton::Digit0:ScannerButton::Sample;
        contact(unsigned(key),pressed);
        if(pressed)wavHeld_=key;else wavHeld_.reset();
    }
    void cancelWavStep(){
        if(!wavCancel_.active()||!machine_)return;
        const auto mode=machine_->channel0Mode();
        const auto step=wavCancel_.advance(machine_->ticks,mode.known,mode.high,
            machine_->lcd.line(0),machine_->lcd.line(1),floppyState().idle);
        cancelWavAction(step.action);
        wavStatus_=wavCancel_.label();
        if(!step.done)return;
        if(!step.ok){
            const auto reason=wavCancelReason_+" "+
                (step.error?step.error:"Original firmware did not confirm recovery.");
            wavError(reason.c_str());
            return;
        }
        // The physical drive is idle and original firmware displays Pxx.
        // Restore the user's read-only soundbank (if automatically replaced).
        wavRelease();
        restoreWavOriginalFloppy();
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=false;
        wavStatus_="WAV cancelled safely: original firmware returned to Pxx. "
                   "Previous committed bank preserved; unsaved sample RAM may have changed.";
        error_=wavAutoOsMounted_?
            "WAV cancellation returned to Pxx, but prior floppy could not be restored automatically.":
            "WAV cancelled: previous project bank preserved. Unsaved sample RAM may have changed.";
        ++wavReport_;
    }
    void wavStep(){
        if(!wavCapture_.active()||!machine_||!autoWavSource_)return;''',
        "original firmware cleanup and recovery FSM")
    s=one(s,
        '''            }else wavError(action.error);
        }else wavStatus_=wavCapture_.stageName();''',
        '''            }else beginWavCancel(action.error?
                action.error:"Original firmware WAV capture failed; trying to return to Pxx.");
        }else wavStatus_=wavCapture_.stageName();''',
        "automatic recovery for failures")
    s=one(s,
        '''                wavStep();
                bankStep();''',
        '''                wavStep();
                cancelWavStep();
                bankStep();''',
        "run recovery during real emulated CPU time")
    s=one(s,
        '''        if(wavCapture_.active())wavError("Boot interrupted WAV capture; RAM may have changed.");
        if(bankSave_.active())bankError("Boot interrupted performance bank save; old bank retained.");''',
        '''        if(wavCapture_.active()||wavCancel_.active())
            wavError("Boot interrupted firmware WAV capture/recovery; RAM may have changed.");
        if(bankSave_.active())bankError("Boot interrupted performance bank save; old bank retained.");''',
        "reboot life-cycle")
    s=one(s,
        '''            if(wavCapture_.active())wavError("Restored project interrupted an unfinished WAV import.");
            if(bankSave_.active())bankError("Restored project interrupted an unfinished bank write.");''',
        '''            if(wavCapture_.active()||wavCancel_.active())
                wavError("Restored project interrupted an unfinished WAV import/recovery.");
            if(bankSave_.active())bankError("Restored project interrupted an unfinished bank write.");''',
        "host project reload life-cycle")
    return s

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    actual=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if actual!=PIN:raise RuntimeError(f"P011 wrong pinned emulator core: {actual}")
    source=ENGINE.read_text(encoding="utf-8")
    target=patch(source)
    if a.verify:print("P011 safe firmware cancellation source anchors: PASS");return
    shutil.copyfile(ROOT/"src/125a_firmware_cancel.h",UP/"src/125a_firmware_cancel.h")
    ENGINE.write_text(target,encoding="utf-8",newline="\n")
    print("P011 firmware-safe WAV STOP/EXIT and deferred DISK7 cancel installed")

if __name__=="__main__":main()
