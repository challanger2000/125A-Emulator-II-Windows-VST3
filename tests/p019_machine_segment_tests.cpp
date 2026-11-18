// SPDX-License-Identifier: GPL-3.0-only
// P019: REAL original emulated Z80 + SAR/DRAM hardware segment-invariance test.
// Synthetic short Z80 ROM only: no proprietary E-mu ROM, bank, or OS.
#include "125a_wav_input.h"
#include "machine.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>

namespace {
constexpr std::uint64_t total=900000; // enough for 512 original Z80 SAR reads
void req(bool b,const char* why){if(!b){std::cerr<<"FAIL P019 hardware: "<<why<<"\n";std::exit(1);}}
struct Result{
    std::uint64_t ticks=0,reads=0,conversions=0,unknown=0,dramReads=0,dramWrites=0;
    std::uint16_t pc=0,scannerPc=0;
    double wallMs=0; // native wall stopwatch, NOT virtual EII time
    std::array<std::uint8_t,512> sample{};
};
Result run(std::uint64_t batch){
    auto m=std::make_unique<eii::Machine>();
    static constexpr std::uint8_t code[]={
        0x31,0x00,0x28,
        0x3e,0x34,0xd3,0x1f,0x3e,0x68,0xd3,0x1c,0x3e,0x01,0xd3,0x1c,
        0x3e,0xf8,0xd3,0x70,0x3e,0xff,0xd3,0x78,0x3e,0xf0,0xd3,0x70,
        0x3e,0x3b,0xd3,0x40,
        0x3e,0xcf,0xd3,0x33,0x3e,0x7f,0xd3,0x33,0x3e,0x80,0xd3,0x32,
        0x01,0x00,0x40,0x0b,0x78,0xb1,0x20,0xfb,
        0x21,0x00,0x21,0x06,0x00,0x0e,0x08,
        0xed,0xa2,0xe3,0xe3,0x20,0xfa,
        0x06,0x00,0xed,0xa2,0xe3,0xe3,0x20,0xfa,
        0x3e,0x00,0xd3,0x32,0x76
    };
    std::copy(std::begin(code),std::end(code),m->main.rom.begin());
    auto& port=m->scanner.pio[1];port.mode=3;port.mask=0x3f;port.output=0x80;
    eii::wav::Wav wave;wave.rate=48000;wave.channels=1;wave.mono.resize(48000);
    constexpr double pi=3.14159265358979323846;
    for(std::size_t i=0;i<wave.mono.size();++i)
        wave.mono[i]=float(.25*std::sin(2*pi*1000*double(i)/48000));
    auto src=std::make_shared<eii::wav::Source>(std::move(wave));
    m->sampleInput=src;
    const auto first=std::chrono::steady_clock::now();
    for(std::uint64_t t=0;t<total;){
        const auto step=std::min(batch,total-t);
        m->run(step);
        t+=step;
    }
    req(src->started(),"synthetic original hardware started analog SAMPLE");
    const auto elapsedMs=std::chrono::duration<double,std::milli>(
        std::chrono::steady_clock::now()-first).count();
    Result r;r.wallMs=elapsedMs;r.ticks=m->ticks;r.reads=m->sampleReads;
    r.conversions=m->sampleSar.conversions;
    r.unknown=m->sampleUnknownReads;
    r.dramReads=m->dramReadCycles;r.dramWrites=m->dramWriteCycles;
    r.pc=m->main.cpu.pc;r.scannerPc=m->scanner.cpu.pc;
    for(unsigned i=0;i<512;++i)r.sample[i]=m->memory[0x2100+i];
    return r;
}
void compare(const Result& a,const Result& b,const char* label){
    req(a.ticks==b.ticks,"original 4MHz clock count identical");
    req(a.reads==b.reads&&a.reads==512,"exact hardware Z80/SAR read total");
    req(a.conversions==b.conversions,"SAR conversions unchanged");
    req(a.unknown==b.unknown&&a.unknown==0,"all sampled bytes remain known");
    req(a.dramReads==b.dramReads&&a.dramWrites==b.dramWrites,
        "original DRAM bus activity identical");
    req(a.pc==b.pc&&a.scannerPc==b.scannerPc,
        "main and scanner Z80 program counters identical");
    req(a.sample==b.sample,"512 original Z80 INI DRAM sample bytes bit-identical");
    std::cout<<"P019 hardware segment "<<label<<" exact original Z80/SAR/DRAM PASS\n";
    std::cout<<"P020 synthetic machine throughput "<<label<<": "
             <<b.wallMs<<" ms wall per "<<b.ticks<<" original ticks, "
             <<(b.ticks/4000.0)/b.wallMs*100.0
             <<"% real-time (single sample; CI host dependent, no actual ROM)\n";
}
} // namespace
int main(){
    const auto reference=run(total);
    compare(reference,run(20000),"20k old basic");
    compare(reference,run(60000),"60k new basic");
    compare(reference,run(24000),"24k old DSP");
    compare(reference,run(48000),"48k new DSP");
    std::cout<<"P019 real emulated hardware clocks, registers, sampled PCM: all PASS\n";
}
