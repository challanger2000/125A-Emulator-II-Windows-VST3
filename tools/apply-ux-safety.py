#!/usr/bin/env python3
"""P008: after P006 overlays, retain WAV bank on Eject and auto-mount private writable OS.
Source-pinned; no edits to the upstream hardware model, ROM, OS, or owner's disk files.
"""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"upstream/eii-emu/src/vst3/plugin_engine.h"

def one(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"P008 {label}: expected exactly one source anchor, got {n}")
    return s.replace(old,new)

def patch(s):
    s=one(s,
'''    std::shared_ptr<const std::vector<std::uint8_t>> embeddedBank_;
    mutable std::mutex projectMediaMutex_;''',
'''    std::shared_ptr<const std::vector<std::uint8_t>> embeddedBank_;
    // User's old disk is held untouched during a protected temporary OS import.
    std::shared_ptr<host::FloppyImageBacking> wavPreviousFloppy_;
    bool wavAutoOsMounted_=false;
    mutable std::mutex projectMediaMutex_;''',"working-disk members")
    s=one(s,
'''            if(!producing()||!machine_||!floppyState().mounted){
                error_="125A WAV requires booted EII with OS 3.1 floppy mounted.";return;
            }''',
'''            if(!producing()||!machine_){
                error_="125A WAV requires a running Emulator II.";return;
            }''',"no manual OS disk requirement")
    s=one(s,
'''            error_.clear();projectBusy_.store(true,std::memory_order_release);
            oldSampleSource_=sampleSource_;autoWavSource_=source;''',
'''            // Use original OS3.1 SAMPLE overlay and original DISK7 SAVE BANK,
            // but keep the bundled OS and user's mounted soundbank read-only.
            // All writes go to an independent private in-memory floppy.
            if(!floppyBacking_||!floppyBacking_->writable||floppyBacking_->direct||
               floppyBacking_->hfe){
                if(floppyBacking_&&!floppyState().idle){
                    error_="Floppy is busy; finish its operation before Import WAV.";return;
                }
                try{
                    if(settings_.osImage.empty())throw std::runtime_error(
                        "Cannot find original OS 3.1 in Contents/Resources/OS");
                    host::FloppyImageBacking os(settings_.osImage,false);
                    const auto& raw=os.image->bytes();
                    if(raw.size()!=EmuiiImage::imageBytes||
                       std::all_of(raw.begin(),raw.begin()+portable::bankDataOffset,
                                   [](std::uint8_t b){return b==0;}))
                        throw std::runtime_error("Invalid original OS3.1 image");
                    auto temp=std::make_shared<host::FloppyImageBacking>(
                        std::span<const std::uint8_t>(raw),
                        std::filesystem::path("125A-Temporary-OS31.emuiifd"));
                    // Do not change the machine until validation and allocation
                    // of the entire working medium have succeeded.
                    installFloppy(*machine_,temp);
                    if(!wavAutoOsMounted_){
                        wavPreviousFloppy_=floppyBacking_;
                        wavAutoOsMounted_=true;
                    }
                    floppyBacking_=std::move(temp);floppyHeld_=false;
                    media_="125A protected OS3.1 working disk (automatic WAV import)";
                }catch(const std::exception& ex){
                    error_=std::string("Import WAV: cannot prepare OS3.1: ")+ex.what();
                    return;
                }
            }
            error_.clear();projectBusy_.store(true,std::memory_order_release);
            oldSampleSource_=sampleSource_;autoWavSource_=source;''',"auto RAM-backed OS")
    s=one(s,
'''    void bankRelease(){
        if(bankHeld_){contact(unsigned(*bankHeld_),false);bankHeld_.reset();}
        bankSave_.reset();
    }
    void bankError''',
'''    // Running on the single Machine owner thread; settings_.floppy retains
    // the user's selected image even while the temporary OS is physically in.
    void restoreWavOriginalFloppy(){
        if(!wavAutoOsMounted_)return;
        if(!machine_||!floppyState().idle){
            error_="Temporary OS3.1 floppy stays inserted (drive busy). "
                   "Finish the disk operation or reset to restore the chosen floppy.";
            return;
        }
        try{
            if(wavPreviousFloppy_)installFloppy(*machine_,wavPreviousFloppy_);
            else{
                if(machine_->diskRead){
                    machine_->diskRead->eject(0);
                    machine_->diskRead->persistTrack={};
                }
                if(machine_->floppy.drives[0])machine_->floppy.drives[0]->eject();
                machine_->diskDma.floppyIo=false;
            }
            floppyBacking_=std::move(wavPreviousFloppy_);
            floppyLastSaved_.clear();wavAutoOsMounted_=false;
            media_=floppyBacking_?mediaLabel(*floppyBacking_):"No disk";
        }catch(const std::exception& ex){
            error_=std::string("Bank saved, but floppy restore failed: ")+ex.what();
        }
    }
    void bankRelease(){
        if(bankHeld_){contact(unsigned(*bankHeld_),false);bankHeld_.reset();}
        bankSave_.reset();
    }
    void bankError''',"return original physical disk")
    s=one(s,
'''        bankRelease();
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=true;''',
'''        bankRelease();
        restoreWavOriginalFloppy();
        projectBusy_.store(false,std::memory_order_release);
        wavSuccess_=true;''',"return after original DISK7 save")
    s=one(s,
'''                   "ROM directory must remain available.";
        error_.clear();++wavReport_;''',
'''                   "ROM directory must remain available.";
        if(wavAutoOsMounted_)
            wavStatus_+=" Temporary OS floppy remains mounted; finish disk activity before switching media.";
        else error_.clear();
        ++wavReport_;''',"display incomplete media restore")
    s=one(s,
'''        wavSuccess_=false;++wavReport_;wavRelease();
        projectBusy_.store(false,std::memory_order_release);''',
'''        wavSuccess_=false;++wavReport_;wavRelease();
        // Do not hot-swap during firmware SAMPLE/DISK: restore only after
        // firmware returned to its ordinary Pxx preset display.
        if(wavAutoOsMounted_&&machine_){
            const auto lcd=machine_->lcd.line(0);
            if(lcd.size()>=3&&lcd[0]=='P'&&lcd[1]>='0'&&lcd[1]<='9'&&
               lcd[2]>='0'&&lcd[2]<='9'&&floppyState().idle)
                restoreWavOriginalFloppy();
        }
        projectBusy_.store(false,std::memory_order_release);''',"firmware-safe error recovery")
    s=one(s,
'''        if(bankSave_.active())throw std::runtime_error("Cannot change floppy during original SAVE BANK.");
        if(!machine_)throw std::runtime_error("Boot the machine before inserting a floppy.");''',
'''        if(bankSave_.active()||wavCapture_.active())
            throw std::runtime_error("Cannot change floppy during Import WAV / SAVE BANK.");
        if(!machine_)throw std::runtime_error("Boot the machine before inserting a floppy.");''',"no manual concurrent floppy swap")
    s=one(s,
'''        // A manual media change invalidates the *old* project snapshot.
        embeddedBank_.reset();
        {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}''',
'''        // Eject does not erase original EII sample RAM. Preserve the last
        // committed project bank on Eject and when inserting the same OS.
        // A different soundbank can overwrite RAM: discard the old snapshot
        // instead of falsely recalling its obsolete contents in Studio One.
        if(!path.empty()&&!sameImage(path,settings_.osImage)){
            embeddedBank_.reset();
            {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}
        }
        wavAutoOsMounted_=false;wavPreviousFloppy_.reset();''',"protect DAW project bank on Eject")
    s=one(s,
'''            contacts_={};media_=media;error_=rescued;
            startup_="Production: phase0 / RAM seed1 / controller seed e1122026";''',
'''            contacts_={};media_=media;error_=rescued;
            wavAutoOsMounted_=false;wavPreviousFloppy_.reset();
            startup_="Production: phase0 / RAM seed1 / controller seed e1122026";''',"reset stale temp pointers after boot")
    return s

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    args=ap.parse_args()
    before=ENGINE.read_text(encoding="utf-8")
    if "wavAutoOsMounted_" in before:
        raise RuntimeError("P008 already patched or conflicting source")
    after=patch(before)
    if args.verify:print("P008 original OS auto-mount + Eject project bank retention anchors: PASS")
    else:
        ENGINE.write_text(after,encoding="utf-8",newline="\n")
        print("P008 source-pinned UX/safety patch installed on local upstream copy")
