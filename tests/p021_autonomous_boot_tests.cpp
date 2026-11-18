// SPDX-License-Identifier: GPL-3.0-only
#include "125a_autonomous_boot_timeline.h"
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
using eii::portable::AutonomousBootTimeline;
static void need(bool p,const char* why){
    if(!p){std::cerr<<"FAIL P021 "<<why<<"\n";std::exit(1);}
}
int main(){
    AutonomousBootTimeline t;
    need(!t.active(),"boot accelerator idle unless original machine is booted");
    // No DAW process callbacks: hostTarget remains at position 0 for the
    // ENTIRE simulated 18s original guest start.
    t.begin(170000,100);
    need(t.active(),"original firmware freewheel enabled");
    std::uint64_t guest=170000,hostTarget=0;
    const std::uint64_t start=guest;
    for(unsigned i=0;i<1200;++i){
        const auto step=AutonomousBootTimeline::quantum(false);
        guest+=step;
        need(hostTarget==0,"host clock must remain stopped in zero-callback test");
    }
    need(guest-start==72000000,
         "18 original virtual seconds were executed independently of the DAW");
    need(!t.exceeded(guest,25000),"normal 18s startup remains under watchdog");
    t.handoff(guest,hostTarget);
    need(!t.active(),"genuine original Pxx can finish boot");
    need(t.anchorHostPos()==0&&t.anchoredTarget(0,48000)==guest,
         "postboot first DAW sample maps to the final actual original Z80 tick");
    need(t.anchoredTarget(480,48000)==guest+40000,
         "480 host frames after boot are precisely 40,000 original ticks");
    need(t.relativeFrame(0,512)==-512,
         "new host output must first serve declared latency of silence");
    need(t.relativeFrame(512,512)==0,
         "original first usable ring frame starts at correct host sample");
    need(t.relativeFrame(513,512)==1,"following host frame advances one frame");

    // Another instance booting while DAW has 10,000 frames already: the
    // original song position MUST NOT gain 10k frames or jump MIDI pitch.
    t.begin(100000000,20000);
    guest=100000000;
    const auto step=AutonomousBootTimeline::quantum(true);
    need(step==48000,"DSP worker consumes exactly six 96-frame blocks");
    for(unsigned i=0;i<25;++i)guest+=step;
    t.handoff(guest,10000);
    need(t.anchoredTarget(10000,48000)==guest,
         "already-running DAW timeline re-anchor is exact");
    need(t.anchoredTarget(10480,48000)==guest+40000,
         "new MIDI at host frame 10480 has original 4MHz time");
    need(t.relativeFrame(9500,512)<0,
         "in-flight preboot host callback is always silent");
    need(t.relativeFrame(10512,512)==0,
         "real original audio starts after the exact new reported latency");
    need(t.anchoredTarget(1000,48000)==guest,
         "old before-boot MIDI cannot be mapped before original CPU start");

    // Never spin on broken/missing OS forever.
    t.begin(7,3000);
    need(!t.exceeded(AutonomousBootTimeline::maxBootTicks,3001),
         "watchdog budget is based on ticks SINCE this boot's original reset");
    need(t.exceeded(7+AutonomousBootTimeline::maxBootTicks,3001),
         "guest firmware that never displays Pxx exits autonomous mode");
    t.begin(7,3000);
    need(t.exceeded(7,3000+AutonomousBootTimeline::maxBootWallMs),
         "90s real wall cap prevents starved host CPU hogging forever");
    t.handoff(7,900);
    need(t.anchoredTarget(900,48000)==7,
         "bounded fallback enters original realtime clock without fake Pxx");

    std::cout<<"P021 original 4MHz freewheel with zero host callbacks, exact "
             <<"48k MIDI/audio reanchor and bounded fallback: PASS\n";
}
