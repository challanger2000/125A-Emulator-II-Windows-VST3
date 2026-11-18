// SPDX-License-Identifier: GPL-3.0-only
#include "125a_original_boot_batch.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
using eii::portable::OriginalBootBatch;
static void require(bool b,const char* why){
    if(!b){std::cerr<<"FAIL P019: "<<why<<"\n";std::exit(1);}
}
static std::uint64_t simulate(bool optimized,bool dsp){
    OriginalBootBatch batches;batches.reset();
    std::uint64_t current=0,n=0;
    // Synthetic CPU program with host MIDI/parameter events at precise,
    // non-aligned tick positions. End time and ALL event boundaries match.
    constexpr std::uint64_t target=12*OriginalBootBatch::cpuHz;
    constexpr std::array<std::uint64_t,9> events{
        12345ull,58000ull,100001ull,900342ull,3999999ull,
        4000001ull,8000313ull,9000067ull,11000009ull
    };
    std::size_t eventIndex=0;
    while(current<target){
        const std::uint64_t old=dsp?OriginalBootBatch::normalDsp:OriginalBootBatch::quantumNormal;
        const std::uint64_t step=optimized?batches.quantum(dsp,false,false):old;
        require(step>0 && step%OriginalBootBatch::quantumFine==0,
                "every quantum represents integral original 4 MHz CPU ticks");
        std::uint64_t end=std::min(target,current+step);
        if(eventIndex<events.size())
            end=std::min(end,std::max(current+1,events[eventIndex]));
        require(end>current,"original clock must always advance");
        // Real Engine runs Machine::run(end-current); no tick is omitted.
        current+=end-current;
        ++n;
        if(eventIndex<events.size()&&current==events[eventIndex])++eventIndex;
    }
    require(eventIndex==events.size(),"no MIDI event dropped");
    require(current==target,"exact 48 million original hardware cycles executed");
    return n;
}
int main(){
    OriginalBootBatch state;
    require(state.isReady(),"inactive engine should not run boot boost");
    state.reset();
    require(!state.isReady(),"new original machine reset enables boot-only batches");
    require(state.quantum(false,false,false)==60000,"15ms original-clock basic boot");
    require(state.quantum(true,false,false)==48000,"12ms exact DSP worker block boot");
    require(state.quantum(false,true,false)==4000,"urgent realtime main audio fine 1ms");
    require(state.quantum(true,true,false)==8000,"urgent realtime DSP block 2ms");
    require(state.quantum(false,false,true)==20000,
            "original SAR/sample/foreign project write protected");
    require(state.quantum(true,false,true)==24000,
            "original nonlinear DSP protected during firmware transactions");
    state.ready();
    require(state.quantum(false,false,false)==20000,"Pxx restores normal 5ms scheduling");
    require(state.quantum(true,false,false)==24000,"Pxx restores standard 6ms DSP scheduling");
    for(bool dsp:{false,true}){
        const auto baseline=simulate(false,dsp);
        const auto optimized=simulate(true,dsp);
        require(optimized<baseline,"pre-preset batching reduces machine run invocations");
        require(optimized*2<baseline,"over 50 pct fewer machine run calls for synthetic boot trace");
    }
    std::cout<<"P019 exact 4 MHz boot target/MIDI cutoff, audio urgent guards, fewer run calls: PASS\n";
}
