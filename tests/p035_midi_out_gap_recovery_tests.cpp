// P035: consumer must never join a pre-overflow UART half-message
// with later completed original SCN2651 bytes to invent a VST3 note.
#include "vst3/rt_primitives.h"
#include "125a_original_midi_out.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>

static void check(bool b,const char* why){if(!b)throw std::runtime_error(why);}
int main()try{
    using Q=eii::vst::SpscQueue<eii::vst::midiout::Byte,4>;
    using Byte=eii::vst::midiout::Byte;
    using Parser=eii::vst::midiout::Assembler;
    using Msg=eii::vst::midiout::Message;
    Q q;
    Parser parser;
    std::vector<Msg> messages;
    unsigned dropped=0;
    bool gapPending=false;
    std::uint64_t frame=0;

    // Exact same producer loss handshake as actual PluginEngine, with a
    // smaller deliberately bounded queue to trigger the hard case.
    auto push=[&](std::uint8_t byte){
        const Byte packet{byte,1,1,++frame,std::uint8_t(gapPending)};
        if(!q.push(packet)){++dropped;gapPending=true;}
        else gapPending=false;
    };
    auto consume=[&](){
        while(const Byte* b=q.front()){
            const auto copy=*b;q.pop();
            if(copy.gap)parser.reset();
            Msg msg{};
            if(parser.feed(copy.value,msg))messages.push_back(msg);
        }
    };
    // First complete legitimate note; after it an incomplete second NoteOn.
    push(0x90);push(60);push(100);push(0x90);
    push(62);push(110); // both dropped: the SPSC is full
    check(dropped==2&&gapPending,"two physical UART bytes dropped after full queue");
    consume();
    check(messages.size()==1&&messages[0].status==0x90&&messages[0].data1==60&&
          messages[0].data2==100,"valid pre-overflow note retained");
    // First recovered original byte could be DATA from the middle of a
    // status-running message. It must be orphaned after loss barrier.
    push(67); // first successfully accepted byte after loss, marked gap
    check(!gapPending,"loss marker consumes pending flag on successful push");
    const Byte* barrier=q.front();
    check(barrier&&barrier->gap==1&&barrier->value==67,"producer stamped first physical post-loss byte");
    consume();
    check(messages.size()==1&&parser.orphanData==1,"post-gap data cannot complete stale NoteOn");

    push(0x90);push(62);push(80);
    consume();
    check(messages.size()==2&&messages[1].status==0x90&&messages[1].data1==62&&
          messages[1].data2==80,"new complete post-loss note decoded normally");

    // A second test leaves *only* two bytes of an old 3-byte message
    // before the loss; the next valid recovered two-byte message must
    // immediately establish its own running status and not produce stale note.
    Parser second;
    Msg m{};
    check(!second.feed(0x90,m)&&!second.feed(70,m),"old partial note");
    const Byte recovered{0xc0,1,1,100,true};
    if(recovered.gap)second.reset();
    check(!second.feed(recovered.value,m)&&second.feed(12,m)&&m.status==0xc0&&m.data1==12&&
          m.size==2,"loss barrier accepts fresh ProgramChange, drops stale note");

    // Activation / reboot reset is independent of loss reset.
    second.reset();
    check(!second.feed(88,m)&&second.orphanData==1,"no cross-activation running status");
    check(dropped==2&&q.front()==nullptr,"bounded original MIDI output queue empty");
    std::cout<<"P035 original MIDI OUT SPSC overflow: pre-loss valid messages retained; "
             "first post-loss gap barrier; no ghost NoteOn; subsequent genuine messages PASS\n";
    return 0;
}catch(const std::exception& e){
    std::cerr<<"P035 FAIL "<<e.what()<<"\n";return 1;
}
