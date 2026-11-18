#!/usr/bin/env python3
"""P017: save the actual original HDD image with Studio One; reopen without path.

After P016. The 20 MB (22,597,632 byte) drive is copied only on the owner's
non-audio thread and serialized on the host's state thread. No CPU bypass.
Any incomplete transaction is marked persistent hddpending=1, rather than
silently claiming the user sound bank is present.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENGINE=UP/"src/vst3/plugin_engine.h"
COMPONENT=UP/"src/vst3/eii_vst3.cpp"
STATE=UP/"src/vst3/plugin_state.h"
EDITOR=UP/"src/vst3/plugin_editor.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"P017 {label}: expected exactly one source anchor, got {n}")
    return s.replace(a,b,1)

def patch(e,v,s,ed):
    if "captureHddForProject()" in e:raise RuntimeError("P017 already installed")
    for mark in ("ProjectSaveFrame projectSaveFrame()const", "bankMediaWatch_.reset()",
                 "void observeMediaReads()", "void saveCurrentBankInProject()"):
        if mark not in e:raise RuntimeError("P017 requires applied P015/P014: "+mark)
    e=one(e,
        '''    bool projectNeedsBankCapture()const noexcept{''',
        '''    bool projectNeedsHddCapture()const noexcept{
        return hddNeedsSnapshot_.load(std::memory_order_acquire);
    }
    bool projectNeedsBankCapture()const noexcept{''',
        "nonblocking UI HDD project warning")
    e=one(e,
        '#include "125a_live_media_watch.h"',
        '#include "125a_live_media_watch.h"\n#include "125a_portable_hdd.h"',
        "include HDD project serializer")
    v=one(v,
        '#include "125a_portable_state.h"',
        '#include "125a_portable_state.h"\n#include "125a_portable_hdd.h"',
        "component HDD codec")
    s=one(s,
        '    bool bankPendingCapture=false; // song saved with unverified / unfinished live sampler RAM',
        '''    bool bankPendingCapture=false; // song saved with unverified / unfinished live sampler RAM
    bool hddPendingCapture=false; // original HDD not fully snapshotted at save time''',
        "HDD state warning")
    s=one(s,
        '    if(s.bankPendingCapture)o<<"bankpending=1\\n"; // omitted when false for byte-exact legacy compatibility',
        '''    if(s.bankPendingCapture)o<<"bankpending=1\\n"; // omitted when false for byte-exact legacy compatibility
    if(s.hddPendingCapture)o<<"hddpending=1\\n"; // incomplete HDD song state''',
        "write HDD warning")
    s=one(s,
        '        else if(key=="bankpending"){',
        '''        else if(key=="hddpending"){
            if(v!="0"&&v!="1")throw std::runtime_error("Corrupt pending-HDD project marker");
            s.hddPendingCapture=v=="1";
        }
        else if(key=="bankpending"){''',
        "parse HDD warning")
    e=one(e,
        '''    std::shared_ptr<const std::vector<std::uint8_t>> projectMedia_;
    std::atomic<bool> projectBusy_{false};''',
        '''    std::shared_ptr<const std::vector<std::uint8_t>> projectMedia_;
    std::shared_ptr<const std::vector<std::uint8_t>> embeddedHdd_,projectHdd_;
    std::atomic<bool> hddNeedsSnapshot_{false};
    std::uint64_t lastHddWrittenBytes_=0;
    std::atomic<bool> projectBusy_{false};''',
        "immutable HDD state and dirty marker")
    e=one(e,
        '''    struct ProjectSaveFrame{
        std::shared_ptr<const std::vector<std::uint8_t>> bank;
        bool pending=false;
    };
    ProjectSaveFrame projectSaveFrame()const{
        std::lock_guard l(projectMediaMutex_);
        return {projectMedia_,
            projectBusy_.load(std::memory_order_acquire)||
            bankNeedsSnapshot_.load(std::memory_order_acquire)};
    }''',
        '''    struct ProjectSaveFrame{
        std::shared_ptr<const std::vector<std::uint8_t>> bank;
        bool pending=false;
        std::shared_ptr<const std::vector<std::uint8_t>> hdd;
        bool hddPending=false;
    };
    ProjectSaveFrame projectSaveFrame()const{
        std::lock_guard l(projectMediaMutex_);
        return {projectMedia_,
            projectBusy_.load(std::memory_order_acquire)||
            bankNeedsSnapshot_.load(std::memory_order_acquire),
            projectHdd_,hddNeedsSnapshot_.load(std::memory_order_acquire)};
    }
    // Unlike the audio callback, a VST3 host state-save may request a deep
    // copy. Queue it on the sole machine owner, never copy a mutable HardDisk
    // directly from the host thread, never return a partially written sector.
    std::future<bool> captureHddForProject(){
        auto p=std::make_shared<std::promise<bool>>();auto f=p->get_future();
        post([this,p]{
            try{
                if(!machine_||!machine_->hardDisk){
                    // An embedded HDD with autoboot disabled is already a
                    // complete immutable song snapshot; an unmounted external
                    // path is NOT.
                    const bool okay=settings_.hdd.empty()||bool(projectHdd_);
                    if(!okay)hddNeedsSnapshot_.store(true,std::memory_order_release);
                    p->set_value(okay);return;
                }
                if(machine_->hardDisk->phase!=HardDisk::Free||
                   projectBusy_.load(std::memory_order_acquire)){
                    hddNeedsSnapshot_.store(true,std::memory_order_release);
                    p->set_value(false);return;
                }
                const auto& image=machine_->hardDisk->image;
                portable::validateHdd(image);
                auto copy=std::make_shared<const std::vector<std::uint8_t>>(image);
                // Publish a single immutable complete image. The song may be
                // saved immediately after this owner-thread transaction.
                {std::lock_guard l(projectMediaMutex_);projectHdd_=copy;
                  hddNeedsSnapshot_.store(false,std::memory_order_release);}
                if(embeddedHdd_)embeddedHdd_=copy;
                p->set_value(true);
            }catch(...){
                hddNeedsSnapshot_.store(true,std::memory_order_release);
                try{p->set_value(false);}catch(...){}
            }
        });
        return f;
    }''',
        "owner-only safe HDD snapshot and read frame")
    e=one(e,
        '''    void restoreProjectBank(PluginSettings s,
                            std::shared_ptr<const std::vector<std::uint8_t>> bank){''',
        '''    void restoreProjectBank(PluginSettings s,
                            std::shared_ptr<const std::vector<std::uint8_t>> bank){
        restoreProjectMedia(std::move(s),std::move(bank),{});
    }
    void restoreProjectMedia(PluginSettings s,
                            std::shared_ptr<const std::vector<std::uint8_t>> bank,
                            std::shared_ptr<const std::vector<std::uint8_t>> hdd){''',
        "keep existing restore API while adding HDD")
    e=one(e,
        '''        bankNeedsSnapshot_.store(s.bankPendingCapture,std::memory_order_release);
        post([this,s,bank]{''',
        '''        bankNeedsSnapshot_.store(s.bankPendingCapture,std::memory_order_release);
        hddNeedsSnapshot_.store(s.hddPendingCapture,std::memory_order_release);
        {std::lock_guard l(projectMediaMutex_);projectHdd_=hdd;}
        post([this,s,bank,hdd]{''',
        "publish restored HDD before asynchronous host component returns")
    e=one(e,
        '''            embeddedBank_=bank;settings_=s;
            if(bank){
                settings_.hdd.clear();settings_.bootFloppy=true;
                settings_.directImageWrites=false;
            }''',
        '''            embeddedBank_=bank;embeddedHdd_=hdd;settings_=s;
            if(bank&&!hdd){
                settings_.hdd.clear();settings_.bootFloppy=true;
                settings_.directImageWrites=false;
            }
            if(hdd){
                // The embedded HDD takes precedence over any external,
                // possibly missing path. No direct host-file writes.
                settings_.directImageWrites=false;
            }''',
        "restore prefers embedded HDD")
    e=one(e,
        '''            if(s.bankPendingCapture){
                // A song saved mid-import or before original DISK7 completion
                // may include only an older committed bank, or no bank at all.
                // This remains visible after save/reopen; do not claim success.
                bankNeedsSnapshot_.store(true,std::memory_order_release);
                error_="SONG REOPENED WITH UNSAVED EII BANK: only the last committed "
                       "bank is available, NOT the uncommitted live RAM audio. "
                       "Capture via original DISK 7, then save the song again.";
            }''',
        '''            if(s.bankPendingCapture){
                bankNeedsSnapshot_.store(true,std::memory_order_release);
                error_="SONG REOPENED WITH UNSAVED EII BANK: original DISK 7 must "
                       "capture the live RAM bank, then save the song again.";
            }
            if(s.hddPendingCapture){
                hddNeedsSnapshot_.store(true,std::memory_order_release);
                error_="SONG REOPENED WITH INCOMPLETE HDD SNAPSHOT: embedded media "
                       "may be older than last original disk write. Wait for disk "
                       "activity to stop, then save the song again.";
            }''',
        "explicit pending HDD warning on song reopen")
    e=one(e,
        '''    void configure(const PluginSettings& s){post([this,s]{const auto before=settings_;settings_=s;midiTools_.wheelBridge=s.midiWheels;''',
        '''    void configure(const PluginSettings& s){post([this,s]{const auto before=settings_;settings_=s;
        if(before.hdd!=s.hdd){
            embeddedHdd_.reset();
            {std::lock_guard l(projectMediaMutex_);projectHdd_.reset();}
            hddNeedsSnapshot_.store(!s.hdd.empty(),std::memory_order_release);
        }
        midiTools_.wheelBridge=s.midiWheels;''',
        "explicit HDD selection invalidates old song media")
    e=one(e,
        '''            const bool hd=!c.hdd.empty();''',
        '''            const bool hd=!c.hdd.empty()||bool(embeddedHdd_);''',
        "treat restored portable HDD as a physical original HDD")
    e=one(e,
        '''            if(!c.hdd.empty()){
                fresh->installHardDisk(host::loadHddImage(c.hdd));
                if(c.directImageWrites){''',
        '''            if(hd){
                fresh->installHardDisk(embeddedHdd_?
                    std::vector<std::uint8_t>(*embeddedHdd_):host::loadHddImage(c.hdd));
                if(c.directImageWrites&&!embeddedHdd_){''',
        "boot via embedded owner-provided original HDD")
    e=one(e,
        '''            contacts_={};media_=media;error_=rescued;
            // Machine replacement invalidates all prior SIO/HDD counters.''',
        '''            contacts_={};media_=media;error_=rescued;
            lastHddWrittenBytes_=0;
            if(hd&&!embeddedHdd_)
                hddNeedsSnapshot_.store(true,std::memory_order_release);
            // Machine replacement invalidates all prior SIO/HDD counters.''',
        "mark newly loaded external HDD as uncommitted")
    e=one(e,
        '''                machine_->run(n);
                wavStep();''',
        '''                machine_->run(n);
                if(machine_->hardDisk&&
                   machine_->hardDisk->bytesWritten!=lastHddWrittenBytes_){
                    lastHddWrittenBytes_=machine_->hardDisk->bytesWritten;
                    hddNeedsSnapshot_.store(true,std::memory_order_release);
                }
                wavStep();''',
        "mark live original HDD writes after each CPU quantum")
    v=one(v,
        '''            project=eii::portable::decode(text);
            s=eii::vst::parseSettings(project.settings);''',
        '''            project=eii::portable::decodeProject(text);
            s=eii::vst::parseSettings(project.settings);''',
        "decode portable HDD song")
    v=one(v,
        '''        eii::portable::ProjectState project;''',
        '''        eii::portable::PortableProject project;''',
        "P017 project state representation")
    v=one(v,
        '''if(text.size()>(1u<<20))return kResultFalse;''',
        '''if(text.size()>eii::portable::maxProjectStateBytes)return kResultFalse;''',
        "accept up to 40MiB original HDD song state")
    v=one(v,
        '''        engine_->restoreProjectBank(s,std::move(bank));''',
        '''        std::shared_ptr<const std::vector<std::uint8_t>> hdd;
        if(project.hasHdd())
            hdd=std::make_shared<const std::vector<std::uint8_t>>(std::move(project.hdd));
        engine_->restoreProjectMedia(s,std::move(bank),std::move(hdd));''',
        "host state restores validated HDD before original boot")
    v=one(v,
        '''        std::string bytes;
        try{
            const auto frame=engine_?engine_->projectSaveFrame():''',
        '''        // VST3 host state is requested from the non-RT thread. Copy the
        // original HDD only on the emulation owner, with a bounded wait. If
        // busy, preserve the previous image with a persistent warning.
        bool hddComplete=true;
        if(engine_){
            auto f=engine_->captureHddForProject();
            try{hddComplete=f.wait_for(std::chrono::seconds(2))==
                std::future_status::ready && f.get();}
            catch(...){hddComplete=false;}
        }
        std::string bytes;
        try{
            const auto frame=engine_?engine_->projectSaveFrame():''',
        "safe owner-thread copy during DAW save")
    v=one(v,
        '''            const auto b=frame.bank;
            auto current=settings();
            current.bankPendingCapture=frame.pending;
            const auto settingsText=eii::vst::serializeSettings(current);
            bytes=b?eii::portable::encode(settingsText,*b):
                    eii::portable::encode(settingsText);''',
        '''            const auto b=frame.bank;
            const auto h=frame.hdd;
            auto current=settings();
            current.bankPendingCapture=frame.pending;
            current.hddPendingCapture=frame.hddPending||!hddComplete;
            const auto settingsText=eii::vst::serializeSettings(current);
            bytes=eii::portable::encodeProject(settingsText,
                b?std::span<const std::uint8_t>(*b):std::span<const std::uint8_t>{},
                h?std::span<const std::uint8_t>(*h):std::span<const std::uint8_t>{});''',
        "serialize checked full HDD and bank atomically")
    ed=one(ed,
        '''        if(!s.panel.error.empty())o<<L"\\n\\nLast message: "<<wide(s.panel.error);''',
        '''        o<<L"\\nHDD project: "<<
            (backend_.engine().projectNeedsHddCapture()?
                L"UNSAVED/INCOMPLETE - finish HDD access and save song again":
                L"No pending HDD snapshot");
        if(!s.panel.error.empty())o<<L"\\n\\nLast message: "<<wide(s.panel.error);''',
        "visible status: pending original HDD song state")
    return e,v,s,ed

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    args=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P017 original EII kernel mismatch")
    sources=patch(ENGINE.read_text(encoding="utf-8"),
                  COMPONENT.read_text(encoding="utf-8"),
                  STATE.read_text(encoding="utf-8"),
                  EDITOR.read_text(encoding="utf-8"))
    if args.verify:
        print("P017 source anchors: complete portable original HDD state PASS")
        return
    shutil.copyfile(ROOT/"src/125a_portable_hdd.h",UP/"src/125a_portable_hdd.h")
    for path,body in zip((ENGINE,COMPONENT,STATE,EDITOR),sources):
        path.write_text(body,encoding="utf-8",newline="\n")
    print("P017 original HDD project-state capture/boot integrated")

if __name__=="__main__":
    main()
