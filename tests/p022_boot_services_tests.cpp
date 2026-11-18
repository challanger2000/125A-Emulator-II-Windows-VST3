// SPDX-License-Identifier: GPL-3.0-only
#include "125a_preboot_event_policy.h"
#include "125a_autonomous_boot_timeline.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
using namespace eii::portable;
static void check(bool ok,const char* why){if(!ok){std::cerr<<"FAIL P022: "<<why<<"\n";std::exit(1);}}
int main(){
    check(prebootAction(0)==PrebootEventAction::DropMidi,
          "preboot MIDI is rejected, not sent to wrong original-CPU time");
    check(prebootAction(1)==PrebootEventAction::ApplyControl,
          "DAW slider/wheel automation is preserved while original ROM boots");
    for(int i=2;i<255;++i)
        check(prebootAction(std::uint8_t(i))==PrebootEventAction::DropUnknown,
              "unexpected host events never masquerade as controller or MIDI");
    std::array<std::uint8_t,10> events{0,1,1,0,1,0,1,1,0,255};
    unsigned controls=0,midi=0,unknown=0;
    for(auto kind:events){
        switch(prebootAction(kind)){
        case PrebootEventAction::ApplyControl:++controls;break;
        case PrebootEventAction::DropMidi:++midi;break;
        case PrebootEventAction::DropUnknown:++unknown;break;
        }
    }
    check(controls==5&&midi==4&&unknown==1,
          "boot MIDI drop count must never include DAW control automation");
    check(!insertDelayedFloppy(false,0x2800),"no floppy insert if already mounted");
    check(!insertDelayedFloppy(true,0x0000),"HDD boot ROM does not see a floppy early");
    check(!insertDelayedFloppy(true,0x27ff),"original OS resident gate is strict");
    check(insertDelayedFloppy(true,0x2800),"OS in RAM can receive pending floppy");
    check(insertDelayedFloppy(true,0x3000),"overshot original OS resident threshold");
    AutonomousBootTimeline t;
    t.begin(0,1000);
    check(!t.exceeded(4000000*90,1000+90000),
          "a 90s wall startup must continue, not be falsely terminated");
    check(!t.exceeded(4000000*120,1000+150000),
          "previous 130s original boot may progress independently of DAW");
    check(t.exceeded(4000000*180,1000+AutonomousBootTimeline::maxBootWallMs),
          "finite 300s wall fallback still prevents unbounded owner workload");
    check(t.exceeded(AutonomousBootTimeline::maxBootTicks,1001),
          "original guest-tick watchdog protects a firmware infinite loop");
    std::cout<<"P022 original HD-first floppy transition, DAW control/MIDI classification, 300s fallback PASS\n";
}
