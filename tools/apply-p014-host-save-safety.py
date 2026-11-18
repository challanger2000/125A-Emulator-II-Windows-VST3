#!/usr/bin/env python3
"""P014: preserve the host song while a live EII bank is uncommitted.

The P013 getState() "fail closed" returned kResultFalse to the host,
which could result in no song update or a silently missing state.
Now always save a valid state and include a persistent pending-bank warning
whenever the *current* RAM audio is not confirmed by original DISK7.

The previous committed bank is preserved, NEVER replaced with a speculatively
mounted .EII file. On reopen the audible bank may be stale and is labelled as
such: a subsequent original DISK7 capture and another song save are required.

Applies only after the full P013 overlay on the pinned Tuth upstream.
"""
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
STATE=UP/"src/vst3/plugin_state.h"
ENGINE=UP/"src/vst3/plugin_engine.h"
VST=UP/"src/vst3/eii_vst3.cpp"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"P014 {label}: {n} anchors (expected exactly 1)")
    return s.replace(old,new,1)

def patch(st,eng,vst):
    if "bankPendingCapture" in st:
        raise RuntimeError("P014 already applied")
    for marker in ("projectNeedsBankCapture()const noexcept","saveCurrentBankInProject()",
                   "bankNeedsSnapshot_.store(false,std::memory_order_release);"):
        if marker not in eng:raise RuntimeError("P014 requires fully applied P013: "+marker)
    st=one(st,
        '    int recallProgram=-1; // last host program change:',
        '    bool bankPendingCapture=false; // song saved with unverified / unfinished live sampler RAM\n'
        '    int recallProgram=-1; // last host program change:',
        "persistent warning field")
    st=one(st,
        '    o<<"levelmodel=2\\n"; // common level model (level_model.h); absent = older state, migrated on load',
        '    o<<"levelmodel=2\\n"; // common level model (level_model.h); absent = older state, migrated on load\n'
        '    if(s.bankPendingCapture)o<<"bankpending=1\\n"; // omitted when false for byte-exact legacy compatibility',
        "write warning in project settings before calibration")
    st=one(st,
        '        else if(key=="program")s.recallProgram=int(number(v));',
        '        else if(key=="bankpending"){\n'
        '            if(v!="0"&&v!="1")throw std::runtime_error("Corrupt pending-bank project marker");\n'
        '            s.bankPendingCapture=v=="1";\n'
        '        }\n'
        '        else if(key=="program")s.recallProgram=int(number(v));',
        "read and validate pending marker")
    eng=one(eng,
        '''        {std::lock_guard l(projectMediaMutex_);projectMedia_=bank;}
        bankNeedsSnapshot_.store(false,std::memory_order_release);
        post([this,s,bank]{''',
        '''        // Publish an in-progress marker BEFORE replacing the bank;
        // readers must never pair the OLD bank with a cleared marker.
        bankNeedsSnapshot_.store(true,std::memory_order_release);
        {std::lock_guard l(projectMediaMutex_);projectMedia_=bank;}
        bankNeedsSnapshot_.store(s.bankPendingCapture,std::memory_order_release);
        post([this,s,bank]{''',
        "atomic restore bank and marker ordering")
    eng=one(eng,
        '''    bool projectNeedsBankCapture()const noexcept{
        return bankNeedsSnapshot_.load(std::memory_order_acquire);
    }''',
        '''    bool projectNeedsBankCapture()const noexcept{
        return bankNeedsSnapshot_.load(std::memory_order_acquire);
    }
    // One lock-linearized snapshot: VST3 state must never combine an OLD
    // project bank with a "complete" marker from a newer commit.
    struct ProjectSaveFrame{
        std::shared_ptr<const std::vector<std::uint8_t>> bank;
        bool pending=false;
    };
    ProjectSaveFrame projectSaveFrame()const{
        std::lock_guard l(projectMediaMutex_);
        return {projectMedia_,
            projectBusy_.load(std::memory_order_acquire)||
            bankNeedsSnapshot_.load(std::memory_order_acquire)};
    }''',
        "linearized host-state bank plus marker")
    eng=one(eng,
        '''            embeddedBank_.reset();
            {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}
            bankNeedsSnapshot_.store(true,std::memory_order_release);''',
        '''            bankNeedsSnapshot_.store(true,std::memory_order_release);
            embeddedBank_.reset();
            {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}''',
        "mark manual media change pending before invalidating bank")
    eng=one(eng,
        '''                embeddedBank_.reset();
                {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}
                bankNeedsSnapshot_.store(true,std::memory_order_release);''',
        '''                bankNeedsSnapshot_.store(true,std::memory_order_release);
                embeddedBank_.reset();
                {std::lock_guard l(projectMediaMutex_);projectMedia_.reset();}''',
        "mark boot media candidate pending before invalidating bank")
    eng=one(eng,
        '''            if(s.autoBoot&&!s.romFolder.empty())bootNow(false,true);
            else projectBusy_.store(false,std::memory_order_release);''',
        '''            if(s.autoBoot&&!s.romFolder.empty())bootNow(false,true);
            else projectBusy_.store(false,std::memory_order_release);
            if(s.bankPendingCapture){
                // A song saved mid-import or before original DISK7 completion
                // may include only an older committed bank, or no bank at all.
                // This remains visible after save/reopen; do not claim success.
                bankNeedsSnapshot_.store(true,std::memory_order_release);
                error_="SONG REOPENED WITH UNSAVED EII BANK: only the last committed "
                       "bank is available, NOT the uncommitted live RAM audio. "
                       "Capture via original DISK 7, then save the song again.";
            }''',
        "persist warning on project reopen")
    vst=one(vst,
        '        if(engine_&&(engine_->projectSaveBusy()||engine_->projectNeedsBankCapture()))return kResultFalse;',
        '''        // A failed VST3 getState is not guaranteed to trigger another save.
        // Preserve the complete current settings and last validated bank even
        // while import/capture is in progress. The explicit marker prevents
        // mistaking the restored bank for uncommitted RAM changes.''',
        "never silently fail whole song save during input capture")
    vst=one(vst,
        '''            const auto b=engine_?engine_->projectBankSnapshot():nullptr;
            const auto settingsText=eii::vst::serializeSettings(settings());''',
        '''            const auto frame=engine_?engine_->projectSaveFrame():
                eii::vst::PluginEngine::ProjectSaveFrame{};
            const auto b=frame.bank;
            auto current=settings();
            current.bankPendingCapture=frame.pending;
            const auto settingsText=eii::vst::serializeSettings(current);''',
        "transactional last-committed-bank plus pending marker")
    return st,eng,vst

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P014 pinned upstream mismatch: "+sha)
    targets=patch(STATE.read_text(encoding="utf-8"),
                  ENGINE.read_text(encoding="utf-8"),
                  VST.read_text(encoding="utf-8"))
    if a.verify:
        print("P014 VST3 non-failing pending-bank project save anchors: PASS")
        return
    for path,s in zip((STATE,ENGINE,VST),targets):
        path.write_text(s,encoding="utf-8",newline="\n")
    print("P014 safe full-song project settings + bankpending marker installed")

if __name__=="__main__":main()
