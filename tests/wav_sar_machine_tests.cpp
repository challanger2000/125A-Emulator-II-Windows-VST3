// 125A P002: C++23 original EII hardware SAMPLE path integration.
// GPL-3.0-only. Synthetic Z80 program adapted from upstream
// Tuth/eii-emu/tests/sample_analog_tests.cpp (no licensed firmware/media).
#include "125a_wav_input.h"
#include "machine.h"
#include "am6072.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
namespace {
constexpr double pi=3.14159265358979323846;
void req(bool value,const char* s){if(!value){std::cerr<<"FAIL "<<s<<"\n";std::exit(1);}}
struct Result{double pp=0;unsigned crossings=0;std::array<std::uint8_t,512> bytes{};};
Result capture(bool tone){
    auto m=std::make_unique<eii::Machine>();
    constexpr std::uint8_t code[]={
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
    eii::wav::Wav w;w.rate=48000;w.channels=1;w.mono.resize(48000);
    for(std::size_t i=0;i<w.mono.size();++i)
        w.mono[i]=tone?float(.25*std::sin(2*pi*1000*i/48000)):0.f;
    auto src=std::make_shared<eii::wav::Source>(std::move(w));
    src->idle(10000);req(!src->started(),"input only begins during machine sample request");
    m->sampleInput=src;
    m->run(900000);
    req(src->started(),"actual machine requests the WAV");
    req(m->sampleReads==512,"512 original Z80 INI/SAR reads");
    req(m->sampleUnknownReads==0,"every SAR byte known");
    req(m->sampleSar.conversions>=512,"SAR conversions active");
    Result r;double iint=0,low=1e10,high=-1e10,previous=0;
    for(unsigned i=0;i<512;++i){
        const std::uint8_t byte=m->memory[0x2100+i];r.bytes[i]=byte;
        const auto d=eii::analog::Am6072::eiiSteadyVolts({byte,255},{4.98046875,true});
        req(d.known,"known analog DAC byte");
        iint-=(200*iint+10000*d.value)/10200;
        if(i>=256){low=std::min(low,iint);high=std::max(high,iint);
            if(i>256&&(iint<0)!=(previous<0))++r.crossings;
            previous=iint;}
    }
    r.pp=high-low;
    std::cout<<(tone?"tone":"silence")<<" Vpp="<<r.pp
             <<" crossings="<<r.crossings<<"\n";
    return r;
}
}
int main(){
    const auto a=capture(true),z=capture(false);
    // Original timer: 10 MHz / 360 = 27777.78 SAR bytes/sec.
    // 256 cells @ 1kHz => about 18 sign crossings.
    req(a.crossings>=16&&a.crossings<=20,"actual 1kHz capture frequency");
    req(a.pp>0.7&&a.pp<2.5,"analog amplitude of imported 0.25V input");
    req(a.pp>z.pp+0.5,"silence negative control must not resemble audio");
    unsigned changed=0;for(unsigned i=0;i<512;++i)changed+=a.bytes[i]!=z.bytes[i];
    req(changed>300,"DRAM bytes causally depend on actual input waveform");
    std::cout<<"WAV -> analog -> SAR -> real Z80 INI -> DRAM: PASS\n";
}
