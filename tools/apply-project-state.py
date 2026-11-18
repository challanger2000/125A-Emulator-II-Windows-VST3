#!/usr/bin/env python3
"""125A P004: original firmware SAVE BANK + project-embedded full floppy media.
Run only AFTER P001 and P003 source-pinned local build overlays.
Does not publish or change Tuth upstream GitHub; NEVER includes ROM/OS files.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENGINE=UP/"src/vst3/plugin_engine.h"
COMPONENT=UP/"src/vst3/eii_vst3.cpp"
BACKING=UP/"src/floppy_image_backing.h"
VERSION="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(text,needle,replacement,name):
    n=text.count(needle)
    if n!=1:raise RuntimeError(f"P004 {name} changed in upstream/local overlay ({n} occurrences)")
    return text.replace(needle,replacement,1)

def main():
    args=argparse.ArgumentParser()
    args.add_argument("--verify",action="store_true")
    opt=args.parse_args()
    version=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if version!=VERSION:raise RuntimeError("P004 upstream version mismatch; fresh audit required")
    eng=ENGINE.read_text(encoding="utf-8")
    comp=COMPONENT.read_text(encoding="utf-8")
    backing=BACKING.read_text(encoding="utf-8")
    if "projectBankSnapshot()" in eng or "125a_portable_state.h" in comp:
        raise RuntimeError("P004 project media already integrated; do not double-patch")

    backing=one(backing,
        " FloppyImageBacking(std::filesystem::path source,bool directWrites,",
        """ // In-memory project media never require extracted/temp disk files.
 FloppyImageBacking(std::span<const std::uint8_t> raw,std::filesystem::path display):
  path(std::move(display)),image(std::make_shared<EmuiiImage>(
      std::vector<std::uint8_t>(raw.begin(),raw.end()))){}
 FloppyImageBacking(std::filesystem::path source,bool directWrites,""",
        "in-memory bank image constructor")

    eng=one(eng,
        '#include "125a_firmware_capture.h"',
        '#include "125a_firmware_capture.h"\n#include "125a_bank_save.h"',
        "owner SAVE BANK include")
    eng=one(eng,
        '    std::string wavStatus_="Idle";',
        """    portable::FirmwareBankSave bankSave_;
    std::optional<ScannerButton> bankHeld_;
    std::shared_ptr<const std::vector<std::uint8_t>> embeddedBank_;
    mutable std::mutex projectMediaMutex_;
    std::shared_ptr<const std::vector<std::uint8_t>> projectMedia_;
    std::atomic<bool> projectBusy_{false};
    std::string wavStatus_="Idle";""",
        "owner permanent project-bank state")

    eng=one(eng,
        '    // UI file decoding is complete before this command.',
        """    // The VST3 project host may call this without driving process().
    // Reading the immutable published bank does NOT touch Machine/real-time.
    std::shared_ptr<const std::vector<std::uint8_t>> projectBankSnapshot()const {
        std::lock_guard l(projectMediaMutex_);return projectMedia_;
    }
    bool projectSaveBusy()const noexcept{return projectBusy_.load(std::memory_order_acquire);}
    // VST3 setState: original project settings + checked embedded disk.
    // Stage a complete bank before the asynchronous hardware reboot; the
    // project can be re-saved even if the host does not process another block.
    void restoreProjectBank(PluginSettings s,
                            std::shared_ptr<const std::vector<std::uint8_t>> bank){
        {std::lock_guard l(projectMediaMutex_);projectMedia_=bank;}
        post([this,s,bank]{
            if(wavCapture_.active())wavError("Restored project interrupted an unfinished WAV import.");
            if(bankSave_.active())bankError("Restored project interrupted an unfinished bank write.");
            embeddedBank_=bank;settings_=s;
            if(bank){
                settings_.hdd.clear();settings_.bootFloppy=true;
                settings_.directImageWrites=false;
            }
            midiTools_.wheelBridge=s.midiWheels;midiTools_.noteOffZero=s.noteOffZero;
            recallProgram_.store(s.recallProgram);
            if(s.autoBoot&&!s.romFolder.empty())bootNow(false,true);
            else projectBusy_.store(false,std::memory_order_release);
        });
    }
    // UI file decoding is complete before this command.""",
        "public state API")

    eng=one(eng,
        '            if(wavCapture_.active()){error_="125A WAV import already running.";return;}',
        '''            if(wavCapture_.active()||bankSave_.active()){error_="125A WAV import or bank save already running.";return;}''',
        "ongoing project media guard")
    eng=one(eng,
        '            error_.clear();\n            oldSampleSource_=sampleSource_;',
        '''            error_.clear();projectBusy_.store(true,std::memory_order_release);
            oldSampleSource_=sampleSource_;''',
        "mark project save busy")
    eng=one(eng,
        '    void cancelAutoWav(){\n        post([this]{if(wavCapture_.active())\n            wavError("WAV cancelled; emulated sample RAM may already have changed.");});\n    }',
        '''    void cancelAutoWav(){
        post([this]{
            if(wavCapture_.active())wavError("WAV cancelled; volatile sample RAM may have changed.");
            if(bankSave_.active())bankError("Bank save cancelled; old project bank retained.");
        });
    }''',
        "cancel either firmware phase")
    eng=one(eng,
        '        if(wavCapture_.active())wavError("Boot interrupted WAV capture; RAM may have changed.");',
        '''        if(wavCapture_.active())wavError("Boot interrupted WAV capture; RAM may have changed.");
        if(bankSave_.active())bankError("Boot interrupted performance bank save; old bank retained.");''',
        "boot phase stop")
    eng=one(eng,
        '        if(!machine_)throw std::runtime_error("Boot the machine before inserting a floppy.");',
        '''        if(bankSave_.active())throw std::runtime_error("Cannot change floppy during original SAVE BANK.");
        if(!machine_)throw std::runtime_error("Boot the machine before inserting a floppy.");''',
        "mount conflict")
    eng=one(eng,
        '        floppyBacking_=std::move(fresh);floppyLastSaved_.clear();settings_.floppy=path;',
        '''        floppyBacking_=std::move(fresh);floppyLastSaved_.clear();settings_.floppy=path;
        // A manual media change invalidates the *old* project snapshot.
        embeddedBank_.reset();
        {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}''',
        "media invalidation")

    eng=one(eng,
        '            if(!c.floppy.empty()){\n                freshFloppy=std::make_shared<host::FloppyImageBacking>(c.floppy,c.directImageWrites,',
        '''            if(embeddedBank_||!c.floppy.empty()){
                if(embeddedBank_){
                    if(embeddedBank_->size()!=EmuiiImage::imageBytes)
                        throw std::runtime_error("Invalid embedded EII bank image length");
                    // The saved state carries bank bytes only, not the OS.
                    // Restore the OS from the locally installed owner disk.
                    const auto path=!c.osImage.empty()?c.osImage:c.floppy;
                    if(path.empty())throw std::runtime_error(
                        "Original Emulator II OS3.1 disk required for project recall");
                    host::FloppyImageBacking os(path,false);
                    const auto original=os.image->bytes();
                    if(original.size()<portable::bankDataOffset)
                        throw std::runtime_error("Original EII OS region is unavailable");
                    if(std::all_of(original.begin(),
                                   original.begin()+portable::bankDataOffset,
                                   [](std::uint8_t x){return x==0;}))
                        throw std::runtime_error("Original EII OS region is empty");
                    auto image=std::vector<std::uint8_t>(*embeddedBank_);
                    std::copy_n(original.begin(),portable::bankDataOffset,image.begin());
                    freshFloppy=std::make_shared<host::FloppyImageBacking>(
                        std::span<const std::uint8_t>(image),
                        std::filesystem::path("125A-Project-Embedded.emuiifd"));
                }else freshFloppy=std::make_shared<host::FloppyImageBacking>(c.floppy,c.directImageWrites,''',
        "embedded disk boot media")

    eng=one(eng,
        '                machine_->run(n);\n                wavStep();',
        '                machine_->run(n);\n                wavStep();\n                bankStep();',
        "run native firmware save state machine")
    eng=one(eng,
        '    void wavError(const char* message){',
        '''    void bankRelease(){
        if(bankHeld_){contact(unsigned(*bankHeld_),false);bankHeld_.reset();}
        bankSave_.reset();
    }
    void bankError(const char* message){
        bankRelease();
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=false;
        wavStatus_=message?message:"Original SAVE BANK failed";
        error_="125A bank save failed: "+wavStatus_;
        ++wavReport_;
    }
    void bankAction(portable::SaveAction a){
        using A=portable::SaveAction;
        ScannerButton key=ScannerButton::Disk;bool down=false;
        switch(a){
        case A::DiskDown:case A::ExitDown:key=ScannerButton::Disk;down=true;break;
        case A::DiskUp:case A::ExitUp:key=ScannerButton::Disk;break;
        case A::SaveDown:key=ScannerButton::Digit7;down=true;break;
        case A::SaveUp:key=ScannerButton::Digit7;break;
        case A::YesDown:key=ScannerButton::Digit9;down=true;break;
        case A::YesUp:key=ScannerButton::Digit9;break;
        default:return;
        }
        contact(unsigned(key),down);
        if(down)bankHeld_=key;else bankHeld_.reset();
    }
    void bankStep(){
        if(!bankSave_.active()||!machine_||!floppyBacking_)return;
        const auto* disk=machine_->diskRead.get();
        if(!disk){bankError("Disk controller absent during SAVE BANK");return;}
        const auto step=bankSave_.advance(machine_->ticks,
            machine_->lcd.line(0),machine_->lcd.line(1),
            disk->writeFrames,disk->writeErrors,floppyState().idle);
        bankAction(step.action);
        if(!step.done){wavStatus_=bankSave_.label();return;}
        if(!step.ok){bankError(step.error);return;}
        const auto raw=floppyBacking_->serialized();
        if(raw.size()!=EmuiiImage::imageBytes){bankError("Original bank has unexpected disk size");return;}
        // Publish only after original firmware completed the entire disk
        // and returned to performance mode. Project getState may read it.
        auto bankOnly=std::make_shared<std::vector<std::uint8_t>>(raw.begin(),raw.end());
        std::fill_n(bankOnly->begin(),portable::bankDataOffset,0);
        std::shared_ptr<const std::vector<std::uint8_t>> copy=bankOnly;
        {std::lock_guard l(projectMediaMutex_);projectMedia_=copy;}
        embeddedBank_=copy;
        bankRelease();
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=true;
        wavStatus_="Original EII recorded the WAV, saved full 573440-byte bank using DISK 7, "
                   "and returned to Pxx. Bank now embedded in VST3 project state; "
                   "ROM directory must remain available.";
        error_.clear();++wavReport_;
    }
    void wavError(const char* message){''',
        "owner SAVE BANK automation")
    eng=one(eng,
        '        wavSuccess_=false;++wavReport_;wavRelease();',
        '''        wavSuccess_=false;++wavReport_;wavRelease();
        projectBusy_.store(false,std::memory_order_release);''',
        "wav failure unblocks prior committed state")
    eng=one(eng,
        '''            if(action.success){
                wavStatus_="Emulator-II firmware accepted WAV (Sample is good) and returned to Pxx. "
                           "The voice lives in volatile sampler RAM, root MIDI 48. "
                           "DAW save/reopen is NOT supported by this milestone.";
                wavSuccess_=true;++wavReport_;wavRelease();
            }else wavError(action.error);''',
        '''            if(action.success){
                wavRelease();
                // Preserve original disk on the host. SAVE BANK writes only
                // to the emulator's protected, private writable copy.
                if(!floppyBacking_||!floppyBacking_->writable||
                   floppyBacking_->direct||floppyBacking_->hfe||!floppyState().idle||
                   !machine_->diskRead||machine_->diskRead->writeErrors){
                    bankError("WAV captured in RAM, but safe EMUIIFD project-bank writing "
                              "needs mounted writable protected-copy floppy (direct writes OFF).");
                }else{
                    const auto first=bankSave_.begin(machine_->ticks,machine_->diskRead->writeFrames);
                    bankAction(first.action);wavStatus_=bankSave_.label();
                }
            }else wavError(action.error);''',
        "firmware WAV completed -> original bank transaction")

    comp=one(comp,
        '#include "vst3/eii_vst3_ids.h"',
        '#include "vst3/eii_vst3_ids.h"\n#include "125a_portable_state.h"',
        "component codec include")
    comp=one(comp,
        '        eii::vst::PluginSettings s;\n        try{s=eii::vst::parseSettings(text);}catch(...){return kResultFalse;}',
        '''        eii::vst::PluginSettings s;
        eii::portable::ProjectState project;
        try{
            project=eii::portable::decode(text);
            s=eii::vst::parseSettings(project.settings);
        }catch(...){return kResultFalse;}''',
        "component transactional state validation")
    comp=one(comp,
        '        if(s.autoBoot&&!s.romFolder.empty())engine_->boot(s,false,true);else engine_->configure(s);',
        '''        // Publish a complete validated in-memory project bank before
        // scheduling the original hardware boot. No media extraction files.
        std::shared_ptr<const std::vector<std::uint8_t>> bank;
        if(project.hasBank())
            bank=std::make_shared<const std::vector<std::uint8_t>>(std::move(project.bank));
        engine_->restoreProjectBank(s,std::move(bank));''',
        "component restore through original boot")
    comp=one(comp,
        '''        const auto text=eii::vst::serializeSettings(settings());
        int32 written=0;return stream->write(const_cast<char*>(text.data()),int32(text.size()),&written)==kResultOk&&written==int32(text.size())?kResultOk:kResultFalse;''',
        '''        if(engine_&&engine_->projectSaveBusy())return kResultFalse;
        std::string bytes;
        try{
            const auto b=engine_?engine_->projectBankSnapshot():nullptr;
            const auto settingsText=eii::vst::serializeSettings(settings());
            bytes=b?eii::portable::encode(settingsText,*b):
                    eii::portable::encode(settingsText);
        }catch(...){return kResultFalse;}
        int32 written=0;return stream->write(bytes.data(),int32(bytes.size()),&written)==kResultOk&&written==int32(bytes.size())?kResultOk:kResultFalse;''',
        "component embedded original bank save")

    if opt.verify:
        print("P004 original-firmware bank save and VST3 IBStream state patch: anchors PASS")
        return
    shutil.copyfile(ROOT/"src/125a_bank_save.h",UP/"src/125a_bank_save.h")
    shutil.copyfile(ROOT/"src/125a_portable_state.h",UP/"src/125a_portable_state.h")
    BACKING.write_text(backing,encoding="utf-8",newline="\n")
    ENGINE.write_text(eng,encoding="utf-8",newline="\n")
    COMPONENT.write_text(comp,encoding="utf-8",newline="\n")
    print("P004 installed into local source-pinned EII VST3 checkout")

if __name__=="__main__":
    main()
