// P035. License: GPL-3.0-only.
//
// Original Z80 instruction execution -> original Machine I/O port 4 ->
// SCN2651 8N1 shift/holding registers -> completed timed bytes ->
// P034 MIDI channel-voice assembler.
// NO proprietary firmware, disks, sound banks or preset shortcuts. The
// program below is a synthetic Z80 ROM, not an original E-mu firmware image.
#include "machine.h"
#include "125a_original_midi_out.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
using Tx=eii::MidiSerial2651::TxFrame;
using Msg=eii::vst::midiout::Message;
using Parsed=std::pair<Msg,std::uint64_t>;

void check(bool value,const char* message) {
    if(!value)throw std::runtime_error(message);
}
struct Result {
    std::vector<Tx> bytes;
    std::vector<Parsed> messages;
    std::string legacyTrace;
    std::uint64_t ticks=0,completed=0,rejected=0,overruns=0,drops=0;
};

std::vector<std::uint8_t> program(bool txEnable) {
    // True original Z80 opcodes; no direct changes to emulated MIDI state.
    // IN3 resets the original serial mode-pointer, OUT6 sets MR1/MR2,
    // OUT7 sets command with external 500kHz/16 8N1 and RxEN|TxEN.
    // Each transmitted byte uses the authentic TXRDY (SR0) poll on IN1;
    // the CPU is allowed to fill a holding register while shifting.
    std::vector<std::uint8_t> bytes={
        0xf3,              // DI
        0xdb,0x03,         // IN A,(3) mode pointer reset
        0x3e,0x4e,0xd3,0x06, // MR1 = 8N1 / external clock
        0xaf,0xd3,0x06,   // MR2 = 0
        0x3e,std::uint8_t(txEnable?0x27:0x24),0xd3,0x07
    };
    // Actual MIDI channel messages, running status (second note without
    // 0x90), interleaved realtime F8, NoteOff, CC, ProgramChange, PitchBend.
    // The complete TX string comes from actual Z80 OUT4 instructions.
    const std::array<std::uint8_t,20> payload{
        0x90,60,100,   // note on
        0xF8,          // MIDI realtime interleaved inside a running status stream
        62,80,         // running-status second note
        0x80,60,0,     // note off
        0xB0,64,127,   // sustain pedal
        0xC0,7,        // program
        0xE0,0,64,     // pitch bend center
        0x90,62,0      // note on velocity 0, equivalent note off
    };
    for(const auto byte:payload){
        if(txEnable){
            // IN A,(01); AND 1; JR Z,-6 = wait until original UART THR free.
            bytes.insert(bytes.end(),{0xdb,0x01,0xe6,0x01,0x28,0xfa});
        }
        bytes.insert(bytes.end(),{0x3e,byte,0xd3,0x04}); // Z80 OUT (4),A
    }
    bytes.push_back(0x76); // HALT once all byte writes are done
    check(bytes.size()<8192,"synthetic fixture fits emulated PROM");
    return bytes;
}

Result run(bool segmented,bool enabled) {
    auto m=std::make_unique<eii::Machine>();
    m->main.rom.fill(0x76); // synthetic halted PROM, never original ROM
    m->scanner.rom.fill(0x76);
    const auto rom=program(enabled);
    std::copy(rom.begin(),rom.end(),m->main.rom.begin());
    constexpr std::uint64_t total=130000;
    std::uint64_t done=0;
    while(done<total){
        const auto quantum=segmented?
           std::min<std::uint64_t>(total-done,
               done%5==0?1:done%5==1?47:done%5==2?307:done%5==3?4000:123):
           total-done;
        m->run(quantum);
        done+=quantum;
    }
    Result result;
    result.ticks=m->ticks;
    result.completed=m->midiSerial.txCompleted;
    result.rejected=m->midiSerial.txRejected;
    result.drops=m->midiSerial.txDropped;
    result.overruns=m->midiSerial.overruns;
    result.legacyTrace=m->serialTx;
    Tx tx{};
    eii::vst::midiout::Assembler parser;
    Msg msg{};
    while(m->midiSerial.popTx(tx)){
        result.bytes.push_back(tx);
        if(parser.feed(tx.byte,msg))result.messages.emplace_back(msg,tx.tick);
    }
    check(m->midiSerial.txPending()==0,"all original UART completion observations drained");
    check(parser.orphanData==0,"original Z80 transmitter produced no orphan MIDI data");
    if(enabled){
        check(parser.completed==7,"original Z80 firmware emitted all seven channel messages");
        check(parser.unsupportedRealtime==1,"original MIDI realtime F8 is not a fake note");
        check(result.completed==20&&result.bytes.size()==20,
              "all 20 physical original MIDI bytes finished at 31250 baud");
        check(result.drops==0&&result.rejected==0,
              "correct original firmware TXRDY polling never rejects/drops bytes");
        check(result.legacyTrace.size()==20,"legacy diagnostic trace retains firmware OUT4");
    }else{
        check(result.bytes.empty()&&result.messages.empty(),
              "TxEN disabled: synthetically programmed Z80 must never create MIDI output");
        check(result.completed==0&&result.rejected==20,
              "SCN2651 refuses each real Z80 OUT4 while transmit disabled");
    }
    return result;
}

void same(const Result& a,const Result& b) {
    check(a.bytes.size()==b.bytes.size()&&a.messages.size()==b.messages.size(),
          "Machine::run segment boundaries do not lose original MIDI frames");
    for(std::size_t i=0;i<a.bytes.size();++i){
        check(a.bytes[i].byte==b.bytes[i].byte&&a.bytes[i].tick==b.bytes[i].tick,
              "original CPU UART cycle timestamp invariant under runtime quantum");
    }
    for(std::size_t i=0;i<a.messages.size();++i){
        const auto& x=a.messages[i];const auto& y=b.messages[i];
        check(x.first.status==y.first.status&&x.first.data1==y.first.data1&&
              x.first.data2==y.first.data2&&x.first.size==y.first.size&&
              x.second==y.second,
              "actual Z80→TX→MIDI message and completion time invariant");
    }
    check(a.legacyTrace==b.legacyTrace&&a.completed==b.completed&&
          a.rejected==b.rejected&&a.drops==b.drops,
          "original CPU source and UART diagnostic counts invariant");
}
void message(const Result& r,unsigned i,int s,int d1,int d2,int size){
    check(i<r.messages.size(),"original Z80 channel voice count");
    const auto& m=r.messages[i].first;
    check(m.status==s&&m.data1==d1&&m.data2==d2&&m.size==unsigned(size),
          "original UART MIDI bytes -> exact P034 decoder channel message");
}
}

int main()try{
    const auto single=run(false,true);
    const auto pieces=run(true,true);
    same(single,pieces);
    check(single.ticks==130000,"both original 4MHz execution timelines completed");
    check(single.bytes.front().tick>=1280&&single.bytes.back().tick<130000,
          "real Z80 first and last UART completion inside valid original timeline");
    for(std::size_t i=1;i<single.bytes.size();++i){
        check(single.bytes[i].tick>=single.bytes[i-1].tick+1280,
              "no SCN2651 outgoing character is transmitted faster than MIDI wire rate");
        check(single.bytes[i].byte<128||single.bytes[i].byte>=128,
              "all eight original UART bits delivered intact");
    }
    message(single,0,0x90,60,100,3);
    message(single,1,0x90,62,80,3);
    message(single,2,0x80,60,0,3);
    message(single,3,0xb0,64,127,3);
    message(single,4,0xc0,7,0,2);
    message(single,5,0xe0,0,64,3);
    message(single,6,0x90,62,0,3);
    // Terminal CPU output confirms authenticity: bytes did not originate
    // from a fake host callback or P034 parser injection.
    check(single.legacyTrace==std::string(
        "\x90\x3c\x64\xf8\x3e\x50\x80\x3c\x00\xb0\x40\x7f\xc0\x07\xe0\x00\x40\x90\x3e\x00",20),
        "real Z80 OUT4 emitted all exact physical original MIDI bytes");
    const auto disabled=run(false,false);
    check(disabled.legacyTrace.size()==20,
          "original disabled SCN2651 does not merely drop CPU instructions");
    std::cout<<"P035 PASS original Z80 instructions -> SCN2651 status/THR/shift "
             "-> timestamped 31250baud MIDI OUT -> real P034 channel parser; "
             "20/20 bytes, seven messages, byte exact independent of CPU batching "
             "and TxEN disabled negative control\n";
    return 0;
}catch(const std::exception& e){
    std::cerr<<"P035 FAIL "<<e.what()<<"\n";
    return 1;
}
