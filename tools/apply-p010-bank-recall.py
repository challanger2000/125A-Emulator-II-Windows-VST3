#!/usr/bin/env python3
"""P010 selected .EII-bank persistence after the P008 source-pinned overlay.

Snapshots the selected, expanded read-only .EII bank into immutable project
media without any OS bytes. Does not pretend to capture modified sample RAM
or a bank loaded from HDD. No private ROMs, images, or WAVs are included.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENGINE=UP/"src/vst3/plugin_engine.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,old,new,name):
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"P010 {name}: expected 1 exact anchor, found {n}")
    return s.replace(old,new,1)

def patch(s):
    if "cloneSelectedBank" in s or "selectedBankFromFloppy" in s:
        raise RuntimeError("P010 was already applied to the current source")
    if "wavAutoOsMounted_" not in s or "projectBankSnapshot()" not in s:
        raise RuntimeError("P010 requires applied P008 and P004 overlays")
    s=one(s,
        '#include "125a_portable_state.h"',
        '#include "125a_portable_state.h"\n#include "125a_selected_bank.h"',
        "selected-bank codec include")

    s=one(s,
        '    std::string mountFloppyNow(const std::filesystem::path& path,bool direct,bool discard){',
        '''    // Convert only explicitly selected .EII files. Ordinary OS floppies,
    // HFE, and EMUIIFD media are NOT assumed to represent a loaded bank.
    static std::shared_ptr<const std::vector<std::uint8_t>> selectedBankFromFloppy(
            const std::shared_ptr<host::FloppyImageBacking>& backing){
        return backing&&backing->bankImport
            ?portable::cloneSelectedBank(backing->serialized())
            :std::shared_ptr<const std::vector<std::uint8_t>>{};
    }
    // Owner-thread publisher; getState reads this immutable pointer only.
    void commitSelectedBank(const std::shared_ptr<const std::vector<std::uint8_t>>& bank){
        if(!bank)return;
        embeddedBank_=bank;
        {std::lock_guard l(projectMediaMutex_);projectMedia_=bank;}
    }
    std::string mountFloppyNow(const std::filesystem::path& path,bool direct,bool discard){''',
        "bank-selection helpers")

    s=one(s,
        '''        if(fresh)installFloppy(*machine_,fresh);
        else{if(machine_->diskRead){machine_->diskRead->eject(0);machine_->diskRead->persistTrack={};}''',
        '''        // Allocate/validate before changing the virtual drive. Failed input
        // must not destroy the preceding committed project bank.
        const auto selectedBank=selectedBankFromFloppy(fresh);
        if(fresh)installFloppy(*machine_,fresh);
        else{if(machine_->diskRead){machine_->diskRead->eject(0);machine_->diskRead->persistTrack={};}''',
        "prepare bank before mount")

    s=one(s,
        '''        if(!path.empty()&&!sameImage(path,settings_.osImage)){
            embeddedBank_.reset();
            {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}
        }
        wavAutoOsMounted_=false;wavPreviousFloppy_.reset();''',
        '''        if(!path.empty()&&!sameImage(path,settings_.osImage)){
            if(selectedBank)commitSelectedBank(selectedBank);
            else{
                // A different non-.EII medium cannot be assumed to match the
                // old bank. Never silently recall the wrong audio.
                embeddedBank_.reset();
                {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}
            }
        }
        wavAutoOsMounted_=false;wavPreviousFloppy_.reset();''',
        "commit selected bank while preserving Eject")

    s=one(s,
        '''            std::shared_ptr<host::DirectImageFile> freshLease;
            if(!c.hdd.empty()){''',
        '''            // A bank chosen as boot media must also survive project save.
            // Restoring a project-supplied snapshot always takes precedence
            // over a stale external path from an older Studio One session.
            const auto bootSelectedBank=!fromState?selectedBankFromFloppy(freshFloppy):
                std::shared_ptr<const std::vector<std::uint8_t>>{};
            std::shared_ptr<host::DirectImageFile> freshLease;
            if(!c.hdd.empty()){''',
        "prepare boot bank before old machine teardown")
    s=one(s,
        '''            contacts_={};media_=media;error_=rescued;
            wavAutoOsMounted_=false;wavPreviousFloppy_.reset();''',
        '''            contacts_={};media_=media;error_=rescued;
            if(bootSelectedBank)commitSelectedBank(bootSelectedBank);
            wavAutoOsMounted_=false;wavPreviousFloppy_.reset();''',
        "commit only after successful boot setup")
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    a=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:
        raise RuntimeError(f"P010 pinned upstream mismatch: {sha}")
    old=ENGINE.read_text(encoding="utf-8")
    new=patch(old)
    if a.verify:
        print("P010 source-anchored .EII selected-bank overlay: PASS")
        return
    shutil.copyfile(ROOT/"src/125a_selected_bank.h",UP/"src/125a_selected_bank.h")
    ENGINE.write_text(new,encoding="utf-8",newline="\n")
    print("P010 selected-bank host-project recall installed in local upstream checkout")

if __name__=="__main__":
    main()
