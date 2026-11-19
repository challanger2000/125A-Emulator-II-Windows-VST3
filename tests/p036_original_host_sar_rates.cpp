// P036: original Z80 -> original sample DAC + S3528 input anti-alias,
// sample-and-hold, MC14559B SAR, -IWAIT, Z80 INI -> original DRAM.
// Feed the production host-audio input queue at multiple real DAW rates.
// No Creative/E-mu private ROM or original floppy is used.
#include "machine.h"
#include "vst3/host_sample_input.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

static constexpr double pi=3.1415926535897932384626433832795;
static void need(bool b,const char* what){if(!b)throw std::runtime_error(what);}

struct Capture {
    int hostRate=0;
    std::array<std::uint8_t,512> pcm{};
    std::uint64_t sarReads=0,conversions=0,waits=0,unknown=0,missing=0,inputDrops=0;
    double amp=0,peak=0;
    unsigned crossings=0;
};

static Capture capture(int rate,bool silence=false,int sampleQuantum=0){
    auto m=std::make_unique<eii::Machine>();
    m->main.rom.fill(0x76); // HALT filler, no proprietary original firmware
    // Taken from independently validated original Z80/ADC/SAR hardware
    // fixture in Tuth's sample_analog_tests; all I/O are CPU instructions.
    static const std::uint8_t code[]{
        0x31,0x00,0x28,                       // stack at 2800
        0x3e,0x34,0xd3,0x1f,0x3e,0x68,0xd3,0x1c,0x3e,0x01,0xd3,0x1c,
        0x3e,0xf8,0xd3,0x70,0x3e,0xff,0xd3,0x78,0x3e,0xf0,0xd3,0x70,
        0x3e,0x3b,0xd3,0x40,
        0x3e,0xcf,0xd3,0x33,0x3e,0x7f,0xd3,0x33,0x3e,0x80,0xd3,0x32,
        0x01,0x00,0x40,0x0b,0x78,0xb1,0x20,0xfb, // settle
        0x21,0x00,0x21,0x06,0x00,0x0e,0x08,
        0xed,0xa2,0xe3,0xe3,0x20,0xfa,          // original INI/DMA-clock pacing
        0x06,0x00,0xed,0xa2,0xe3,0xe3,0x20,0xfa,
        0x3e,0x00,0xd3,0x32,0x76
    };
    std::copy(std::begin(code),std::end(code),m->main.rom.begin());
    // Hardware PB7/PB6 switch levels: select +00dB path, as OS3.1 does.
    auto& b=m->scanner.pio[1];
    b.mode=3;b.mask=0x3f;b.output=0x80;
    auto src=std::make_shared<eii::vst::HostSampleInput>();
    // P021 production host↔original 4MHz ADC mapping; no hostOrigin
    // shift in this fresh (not preboot) synthetic machine fixture.
    src->bind(1,rate,0,0,1.0,0);
    std::vector<float> host(std::size_t(rate),0.0f);
    if(!silence)for(std::size_t i=0;i<host.size();++i)
        host[i]=float(0.5*std::sin(2*pi*1000*double(i)/double(rate)));
    // Real DAW block boundaries, including an odd sample block size.
    const int block=sampleQuantum?sampleQuantum:512;
    for(int off=0;off<rate;off+=block) {
        const int n=std::min(block,rate-off);
        src->push(1,std::uint64_t(off),host.data()+off,nullptr,n,false);
    }
    m->sampleInput=src;
    constexpr std::uint64_t endTicks=3000000;
    // Hardware Z80 runtime may be called in large or tiny CPU dispatches.
    std::uint64_t elapsed=0;
    while(elapsed<endTicks) {
        const auto quantum=sampleQuantum?
            std::min<std::uint64_t>(endTicks-elapsed,elapsed%4==0?9:elapsed%4==1?113:elapsed%4==2?401:12000):
            endTicks-elapsed;
        m->run(quantum); elapsed+=quantum;
    }
    const auto diagnostic=m->report();
    need(diagnostic.find("Original sample input 7-42/7-43:")!=std::string::npos,
         "P036 actual Machine report must not falsely claim analog sample SAR absent");
    need(diagnostic.find("sample-recording/SAR DRAM writes") == std::string::npos,
         "P036 actual original SAR storage must not be listed as UNIMPLEMENTED");
    need(diagnostic.find("SAR conversions=")!=std::string::npos &&
         diagnostic.find("SAR WAIT clocks=")!=std::string::npos &&
         diagnostic.find("analog input steps=")!=std::string::npos,
         "P036 actual hardware recording diagnostics must expose conversion/wait/analog counters");
    Capture c;c.hostRate=rate;c.sarReads=m->sampleReads;
    c.conversions=m->sampleSar.conversions;c.waits=m->sampleWaitClocks;
    c.unknown=m->sampleUnknownReads;c.missing=src->missing.load();c.inputDrops=src->drops.load();
    for(unsigned i=0;i<c.pcm.size();++i)c.pcm[i]=m->memory[0x2100+i];
    // Reconstruct original channel-0 companded delta PCM from real stored
    // bytes. Ignore first 256 bytes (start transients) and measure 1 kHz.
    double iint=0;
    std::array<double,512> y{};
    for(unsigned i=0;i<512;++i) {
        const auto dac=eii::analog::Am6072::eiiSteadyVolts(
            {c.pcm[i],255},{4.98046875,true});
        need(dac.known,"reconstruction DAC code known");
        iint-=(200*iint+10000*dac.value)/10200;
        y[i]=iint;
    }
    double low=1e100,high=-1e100;
    for(unsigned i=257;i<512;++i){
        low=std::min(low,y[i]);high=std::max(high,y[i]);
        if((y[i-1]<0)!=(y[i]<0))++c.crossings;
    }
    c.amp=high-low;c.peak=std::max(std::fabs(low),std::fabs(high));
    std::printf("P036 host=%dHz block=%d sample_reads=%llu conversions=%llu WAIT=%llu input_missing=%llu drops=%llu p-p=%.4fV zeroCrossings=%u\n",
        rate,block,(unsigned long long)c.sarReads,(unsigned long long)c.conversions,
        (unsigned long long)c.waits,(unsigned long long)c.missing,
        (unsigned long long)c.inputDrops,c.amp,c.crossings);
    need(c.sarReads==512&&c.unknown==0&&c.conversions>=512,
         "real original Z80 program recorded 512 known SAR bytes into actual DRAM");
    need(c.waits>0&&c.missing==0&&c.inputDrops==0,
         "real ADC -IWAIT and DAW sample-rate adapter retain all causal host frames");
    if(silence){
        need(c.amp<0.20,"silent host audio cannot fabricate recorded tone");
    }else{
        need(c.amp>2.7&&c.amp<3.6&&c.crossings>=17&&c.crossings<=19,
             "real original analog input -> ADC -> DRAM retains 1kHz 0.5V tone");
    }
    return c;
}

int main()try{
    const auto original48=capture(48000);
    const auto slice48=capture(48000,false,137);
    const auto rate44=capture(44100,false,137);
    const auto rate96=capture(96000,false,256);
    const auto quiet=capture(48000,true,512);
    need(original48.pcm==slice48.pcm,
         "original SAR/DRAM sample bytes bit-identical under host block and Z80 slicing");
    for(const auto* x:{&rate44,&rate96}){
        need(std::abs(x->amp-original48.amp)<0.15,
             "DAW 44.1k/96k input must preserve 48k original SAR amplitude");
        need(x->crossings==original48.crossings,
             "DAW rate changes must not pitch-shift original 1kHz recording");
    }
    need(quiet.amp<original48.amp*0.1,
         "real SAR silence negative control catches fake nonzero recording");
    std::cout<<"P036 PASS real original Z80/IC86 S3528/IC96 C40/MC14559B SAR/-IWAIT/DRAM "
             "with actual VST3 host input 44100/48000/96000Hz, 137/256/512 block slicing; "
             "sound-rate invariance, exact 48k PCM and fail-closed silence\n";
    return 0;
}catch(const std::exception& e){
    std::cerr<<"P036 FAIL "<<e.what()<<"\n";return 1;
}
