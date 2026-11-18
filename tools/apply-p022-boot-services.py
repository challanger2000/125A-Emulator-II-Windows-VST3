#!/usr/bin/env python3
"""P022: restore essential original firmware services during P021 freewheel.

P021 correctly ran hardware clocks without DAW audio, but its new fast-path
skipped the normal advance() side effects: crucially original HDD-first
delayed floppy insertion, DAW slider automation, and throttled slider flush.
It also discarded *all* host events under a MIDI-only error counter and
could leave the output muted if bootNow failed after gating audio.
"""
import argparse
import shutil
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENG=UP/"src/vst3/plugin_engine.h"
TIMELINE=UP/"src/125a_autonomous_boot_timeline.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,old,new,reason):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"P022 {reason}: expected 1 source anchor, got {n}")
    return s.replace(old,new,1)

def patch(e,t):
    for k in ("bool advanceAutonomousBoot(){",
              "void handoffAutonomousBoot(bool playable){",
              "bootGate_.store(false,std::memory_order_release);",
              "void flushThrottle(){",
              "if(floppyHeld_&&machine_&&machine_->main.cpu.pc>=0x2800)",
              "if(presetDisplayed()){",
              "bootMidiDiscarded_.fetch_add(1,std::memory_order_relaxed)"):
        if k not in e:raise RuntimeError("P022 requires verified P021: "+k)
    if "prebootAction(" in e:raise RuntimeError("P022 already installed")
    e=one(e,
        '#include "125a_autonomous_boot_timeline.h"',
        '#include "125a_autonomous_boot_timeline.h"\n#include "125a_preboot_event_policy.h"',
        "original owner preboot service policy")

    e=one(e,
        '''    void bootNow(bool discard,bool fromState){''',
        '''    void bootNow(bool discard,bool fromState){
        // If reset fails AFTER the audio gate closes, the existing
        // instrument must not remain permanently silent.
        bool gatedThisAttempt=false;''',
        "transactional gate closure during boot reset")
    e=one(e,
        '''            bootGate_.store(false,std::memory_order_release);
            // Old pipeline drained''',
        '''            bootGate_.store(false,std::memory_order_release);
            gatedThisAttempt=true;
            // Old pipeline drained''',
        "record actual audio gate closure for fault cleanup")
    e=one(e,
        '''            autonomousBoot_.begin(G_,bootStartMs);
            installAudio();''',
        '''            autonomousBoot_.begin(G_,bootStartMs);
            bootMidiDiscarded_.store(0,std::memory_order_relaxed);
            installAudio();''',
        "reset MIDI drop telemetry per new original hardware boot")
    e=one(e,
        '''            speedTick_=G_;speedTime_=std::chrono::steady_clock::now();speedRatio_=0;
        }catch(const std::exception& e){error_=e.what();}
    }

    // ---- input ----''',
        '''            speedTick_=G_;speedTime_=std::chrono::steady_clock::now();speedRatio_=0;
        }catch(const std::exception& e){
            if(gatedThisAttempt){
                // Even a failed ROM/audio initialization must not strand the
                // host callback's bootGate=false forever.
                try{
                    if(autonomousBoot_.active())handoffAutonomousBoot(false);
                    else bootGate_.store(true,std::memory_order_release);
                }catch(...){bootGate_.store(true,std::memory_order_release);}
            }
            error_=std::string("Original EII boot failed: ")+e.what();
        }
    }

    // ---- input ----''',
        "release host audio gate on original boot failure")

    e=one(e,
        '''        // MIDI arriving before the original firmware has accepted its bank
        // cannot be replayed later at the wrong DAW position. Count and
        // discard it explicitly; project recall remains handled separately.
        while(events_.front()){
            events_.pop();eventDrops_.fetch_add(1,std::memory_order_relaxed);
            bootMidiDiscarded_.fetch_add(1,std::memory_order_relaxed);
        }
        // Drain host preboot audio input''',
        '''        // P021 dropped EVERY host event and thus silently discarded
        // sliders/automation while the OS was booting. Distinguish MIDI
        // note messages from actual DAW control voltage automation.
        // Bound the number of messages handled per pass to keep the
        // original firmware advancing under large event bursts.
        unsigned consumed=0;
        while(consumed<256){
            const HostEvent* ev=events_.front();if(!ev)break;
            switch(portable::prebootAction(ev->kind)){
            case portable::PrebootEventAction::ApplyControl:
                applyEvent(*ev);break; // live CV/slider & project settings
            case portable::PrebootEventAction::DropMidi:
                eventDrops_.fetch_add(1,std::memory_order_relaxed);
                bootMidiDiscarded_.fetch_add(1,std::memory_order_relaxed);
                break;
            case portable::PrebootEventAction::DropUnknown:
                eventDrops_.fetch_add(1,std::memory_order_relaxed);
                break;
            }
            events_.pop();++consumed;
        }
        flushThrottle(); // preserve the same 25 Hz slider scanner policy
        // Original HD-PROM 2.3 "HDD first" boots with the floppy withdrawn.
        // Its resident OS must be allowed to reach 0x2800 before inserting
        // the user's floppy, exactly like the original host-paced advance().
        if(machine_&&portable::insertDelayedFloppy(floppyHeld_,machine_->main.cpu.pc)){
            floppyHeld_=false;
            if(floppyBacking_)installFloppy(*machine_,floppyBacking_);
        }
        // Drain host preboot audio input''',
        "preserve original HD boot order and DAW automation while freewheeling")

    t=one(t,
        'static constexpr std::uint64_t maxBootWallMs=90000;',
        '''// User's prior original-ROM start exceeded 130 s in the DAW. Do
    // not force this independent boot into a stopped host timeline after
    // only 90 s. The 300 s hard limit is an error fallback, never success.
    static constexpr std::uint64_t maxBootWallMs=300000;''',
        "allow real original slow OS startup without false 90-second completion")
    return e,t

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P022 original machine SHA mismatch")
    result=patch(ENG.read_text(encoding="utf-8"),
                 TIMELINE.read_text(encoding="utf-8"))
    if a.verify:
        print("P022 real original boot floppy/automation/fault anchors: PASS")
        return
    shutil.copyfile(ROOT/"src/125a_preboot_event_policy.h",UP/"src/125a_preboot_event_policy.h")
    for path,s in zip((ENG,TIMELINE),result):
        path.write_text(s,encoding="utf-8",newline="\n")
    print("P022 host-independent boot retains original media/DAW automation; gate recovery installed")

if __name__=="__main__":main()
