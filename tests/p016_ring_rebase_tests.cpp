// SPDX-License-Identifier: GPL-3.0-only
#include "vst3/rt_primitives.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
using namespace eii::vst;
static void check(bool yes,const char* msg){
    if(!yes){std::cerr<<"FAIL P016: "<<msg<<"\n";std::exit(1);}
}
int main(){
    using Frame=eii::host::StereoFrame;
    const std::array<Frame,3> audio{{{.left=.125f,.right=-.25f},
                                     {.left=.25f,.right=-.5f},
                                     {.left=.5f,.right=-1.f}}};
    FrameRing ring;
    ring.push(audio);
    for(std::uint64_t i=0;i<3;++i){
        Frame got{};
        check(ring.read(i,got)&&got.left==audio[i].left&&
              got.right==audio[i].right,"ordinary audible samples preserved");
    }
    // 180 s of deliberately dropped host time; only the physical 2.7 s ring
    // is written, whereas the correct virtual address advances 8.64M frames.
    constexpr std::uint64_t gap=180ull*48000;
    ring.pushSilence(gap);
    check(ring.written()==3+gap,"long silence maintains precise absolute frame address");
    for(const auto id:{3+gap-1,3+gap-2,3+gap-FrameRing::capacity}){
        Frame got{.left=42.f,.right=43.f};
        check(ring.read(id,got)&&got.left==0&&got.right==0,
              "all physically retained late silence is actually zero");
    }
    // New audio after a long gap must not inherit stale samples from the
    // wrapped storage, and the next frame must start at the exact tick.
    const std::array<Frame,1> next{{{.left=.75f,.right=-.75f}}};
    ring.push(next);
    Frame resumed{};
    check(ring.read(3+gap,resumed)&&resumed.left==.75f&&resumed.right==-.75f,
          "audio resumes at correct absolute frame after rebase");
    FrameRing full;
    full.push(audio);
    full.pushSilence(FrameRing::capacity*9);
    check(full.written()==3+FrameRing::capacity*9,
          "full unread ring's virtual offset also advances without a long loop");

    ChannelRing chans;
    ChannelRing::Frame initial{};
    initial[2]=.5f;
    chans.push(std::span<const ChannelRing::Frame>(&initial,1));
    ChannelRing::Frame read{};
    check(chans.read(0,read)&&read[2]==.5f,"original individual output unchanged");
    chans.alignTo(gap+1);
    for(const auto id:{gap,gap+1-ChannelRing::capacity}){
        ChannelRing::Frame zero{};
        check(chans.read(id,zero),"late channel silence exists");
        for(float v:zero)check(v==0.f,"no stale jack audio after host rebase");
    }
    ChannelRing::Frame newJack{};
    newJack[3]=.33f;
    chans.push(std::span<const ChannelRing::Frame>(&newJack,1));
    check(chans.read(gap+1,read)&&read[3]==.33f,
          "correct jack mapping when stream resumes");
    chans.alignTo(1);
    check(chans.read(gap+1,read)&&read[3]==.33f,
          "stale alignment cannot move virtual channel pointer backwards");
    std::cout<<"P016 180-s host stall: exact virtual indices, no stale main/aux audio, resume PASS\n";
}
