#!/usr/bin/env python3
"""P013: never equate selecting a .EII floppy with loading its sound into RAM.

A current playable bank can be captured through original firmware DISK7 and
saved into project state. Uses a protected original OS3.1 in-memory floppy,
the existing P004 writer and bank-only serializer, no sample RAM shortcuts.
"""
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENG=UP/"src/vst3/plugin_engine.h"
EDITOR=UP/"src/vst3/plugin_editor.h"
VST=UP/"src/vst3/eii_vst3.cpp"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,a,b,name):
    count=s.count(a)
    if count!=1:raise RuntimeError(f"P013 {name}: {count} expected-one anchors")
    return s.replace(a,b,1)

def patch(e,v,c):
    for mark in ("cancelWavStep()", "inspectHdd", "commitSelectedBank(",
                 "projectSaveBusy()", "restoreWavOriginalFloppy()"):
        if mark not in e:raise RuntimeError("P013 requires P012/P011/P010/P008: "+mark)
    if "saveCurrentBankInProject()" in e:raise RuntimeError("P013 already applied")

    e=one(e,'    bool projectSaveBusy()const noexcept{return projectBusy_.load(std::memory_order_acquire);}',
        '''    bool projectSaveBusy()const noexcept{return projectBusy_.load(std::memory_order_acquire);}
    // A selected floppy is NOT proof that the firmware loaded its bank into RAM.
    // The host must not silently save a song with falsely attributed audio.
    bool projectNeedsBankCapture()const noexcept{
        return bankNeedsSnapshot_.load(std::memory_order_acquire);
    }''',"host state safety guard")
    e=one(e,'    std::atomic<bool> projectBusy_{false};',
        '''    std::atomic<bool> projectBusy_{false};
    std::atomic<bool> bankNeedsSnapshot_{false};
    bool manualBankCommit_=false;''',"live bank state flags")
    e=one(e,
        '''        {std::lock_guard l(projectMediaMutex_);projectMedia_=bank;}
        post([this,s,bank]{''',
        '''        {std::lock_guard l(projectMediaMutex_);projectMedia_=bank;}
        bankNeedsSnapshot_.store(false,std::memory_order_release);
        post([this,s,bank]{''',"restore clears pending capture marker")
    e=one(e,
        '''            error_.clear();projectBusy_.store(true,std::memory_order_release);
            oldSampleSource_=sampleSource_;autoWavSource_=source;''',
        '''            error_.clear();projectBusy_.store(true,std::memory_order_release);
            bankNeedsSnapshot_.store(true,std::memory_order_release);
            oldSampleSource_=sampleSource_;autoWavSource_=source;''',"WAV changes live bank generation")

    e=one(e,'    void cancelAutoWav(){',
        '''    // Explicit, original-firmware-backed current-RAM bank snapshot.
    // Not started by mounting media: loading can happen later and the
    // original RAM often keeps its PREVIOUS bank after eject/insertion.
    void saveCurrentBankInProject(){
        post([this]{
            if(!machine_||!producing()||!presetDisplayed()){
                error_="SAVE BANK: original Emulator II must be running at Pxx.";
                return;
            }
            if(bankSave_.active()||wavCapture_.active()||wavCancel_.active()||
               projectBusy_.load(std::memory_order_acquire)||wavAutoOsMounted_){
                error_="SAVE BANK: another bank or WAV operation is still active.";
                return;
            }
            if(!floppyState().idle){
                error_="SAVE BANK: wait for the original floppy drive to become idle.";
                return;
            }
            if(machine_->diskRead&&machine_->diskRead->writeErrors){
                error_="SAVE BANK: original disk writer recorded errors; reboot before retry.";
                return;
            }
            try{
                if(settings_.osImage.empty())throw std::runtime_error(
                    "Original OS3.1 disk required in plugin Contents/Resources/OS.");
                host::FloppyImageBacking os(settings_.osImage,false);
                const auto raw=os.image->bytes();
                if(raw.size()!=EmuiiImage::imageBytes||
                   std::all_of(raw.begin(),raw.begin()+portable::bankDataOffset,
                       [](std::uint8_t b){return b==0;}))
                    throw std::runtime_error("Invalid private original OS3.1 image.");
                auto temporary=std::make_shared<host::FloppyImageBacking>(
                    std::span<const std::uint8_t>(raw),
                    std::filesystem::path("125A-LiveBank-Temporary-OS31.emuiifd"));
                // No host file is opened for writing; previous media remains
                // in memory, held for restoration AFTER original DISK7 exits.
                installFloppy(*machine_,temporary);
                wavPreviousFloppy_=floppyBacking_;
                wavAutoOsMounted_=true;
                floppyBacking_=std::move(temporary);
                floppyHeld_=false;
                media_="Protected original OS3.1 SAVE BANK working floppy";
                manualBankCommit_=true;
                projectBusy_.store(true,std::memory_order_release);
                const auto first=bankSave_.begin(
                    machine_->ticks,machine_->diskRead->writeFrames);
                bankAction(first.action);
                wavStatus_="Original DISK7: saving live RAM bank into Studio One state";
                error_.clear();
                ++wavReport_;
            }catch(const std::exception& ex){
                error_=std::string("SAVE BANK could not start: ")+ex.what();
                manualBankCommit_=false;
                projectBusy_.store(false,std::memory_order_release);
            }
        });
    }
    void cancelAutoWav(){''',"public manual original bank save")

    e=one(e,
        '''        bankRelease();
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=false;''',
        '''        bankRelease();
        if(manualBankCommit_&&wavAutoOsMounted_&&machine_&&presetDisplayed()&&floppyState().idle)
            restoreWavOriginalFloppy();
        manualBankCommit_=false;
        bankNeedsSnapshot_.store(true,std::memory_order_release);
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=false;''',"fail-closed write safety")
    e=one(e,
        '''        embeddedBank_=copy;
        bankRelease();
        restoreWavOriginalFloppy();
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=true;
        wavStatus_="Original EII recorded the WAV, saved full 573440-byte bank using DISK 7, "
                   "and returned to Pxx. Bank now embedded in VST3 project state; "
                   "ROM directory must remain available.";''',
        '''        embeddedBank_=copy;
        const bool savedLiveBank=manualBankCommit_;
        bankRelease();
        restoreWavOriginalFloppy();
        manualBankCommit_=false;
        bankNeedsSnapshot_.store(false,std::memory_order_release);
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=true;
        wavStatus_=savedLiveBank?
            "Original EII DISK7 saved current RAM bank into project state. Save the song NOW.":
            "Original EII WAV recorded and saved by DISK7 into project state. Save the song NOW.";''',
        "successful original firmware save is the sole project commit")

    e=one(e,
        '''        if(!path.empty()&&!sameImage(path,settings_.osImage)){
            if(selectedBank)commitSelectedBank(selectedBank);
            else{
                // A different non-.EII medium cannot be assumed to match the
                // old bank. Never silently recall the wrong audio.
                embeddedBank_.reset();
                {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}
            }
        }''',
        '''        if(!path.empty()&&!sameImage(path,settings_.osImage)){
            // The selected candidate is NOT the live RAM bank until the
            // firmware actually loads it. Never publish it on mere insertion.
            (void)selectedBank;
            embeddedBank_.reset();
            {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}
            bankNeedsSnapshot_.store(true,std::memory_order_release);
        }''',"stop speculatively publishing mounted bank")
    e=one(e,
        '            if(bootSelectedBank)commitSelectedBank(bootSelectedBank);',
        '''            if(bootSelectedBank){
                // Boot media also is not proof of firmware bank-load success.
                embeddedBank_.reset();
                {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}
                bankNeedsSnapshot_.store(true,std::memory_order_release);
            }''',"stop speculative boot bank publishing")
    e=one(e,
        '''        error_="125A WAV failed: "+wavStatus_;''',
        '''        error_="125A WAV failed: "+wavStatus_;
        bankNeedsSnapshot_.store(true,std::memory_order_release);''',
        "failed WAV changes live bank generation")
    e=one(e,
        '''        wavCancelReason_=std::move(reason);
        wavCancel_.begin(machine_->ticks);''',
        '''        wavCancelReason_=std::move(reason);
        bankNeedsSnapshot_.store(true,std::memory_order_release);
        wavCancel_.begin(machine_->ticks);''',
        "cancelled WAV is pending project bank")

    c=one(c,
        'if(engine_&&engine_->projectSaveBusy())return kResultFalse;',
        'if(engine_&&(engine_->projectSaveBusy()||engine_->projectNeedsBankCapture()))return kResultFalse;',
        "fail closed on uncommitted live RAM during host save")
    v=one(v,
        '''AppendMenuW(menu,MF_STRING,60,L"Status...");''',
        '''AppendMenuW(menu,MF_STRING,25,L"125A: Aktuelle RAM-Bank mit original DISK 7 im Song sichern");
        AppendMenuW(menu,MF_STRING,60,L"Status...");''',
        "manual original bank backup action")
    v=one(v,
        '''        case 30:backend_.updateSettings([&](PluginSettings& x){x.directImageWrites=!s.directImageWrites;});break;''',
        '''        case 25:e.saveCurrentBankInProject();break;
        case 30:backend_.updateSettings([&](PluginSettings& x){x.directImageWrites=!s.directImageWrites;});break;''',
        "bank save menu dispatch")
    v=one(v,
        '''        if(!s.panel.error.empty())o<<L"\\n\\nLast message: "<<wide(s.panel.error);''',
        '''        o<<L"\\nProject bank: "<<
            (backend_.engine().projectNeedsBankCapture()?
                L"LIVE RAM NOT SAVED - use SETTINGS / 125A: Aktuelle RAM-Bank sichern":
                L"No pending bank capture");
        if(!s.panel.error.empty())o<<L"\\n\\nLast message: "<<wide(s.panel.error);''',
        "visible host-state alert")
    return e,v,c

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    actual=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if actual!=PIN:raise RuntimeError("P013 pinned upstream SHA mismatch: "+actual)
    e,v,c=patch(ENG.read_text(encoding="utf-8"),
                EDITOR.read_text(encoding="utf-8"),
                VST.read_text(encoding="utf-8"))
    if a.verify:
        print("P013 original firmware live RAM bank snapshot source anchors: PASS")
        return
    for path,s in ((ENG,e),(EDITOR,v),(VST,c)):
        path.write_text(s,encoding="utf-8",newline="\n")
    print("P013 original DISK7 live RAM snapshot source patch installed")

if __name__=="__main__":
    main()
