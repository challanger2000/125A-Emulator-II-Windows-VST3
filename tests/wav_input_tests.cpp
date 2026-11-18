// SPDX-License-Identifier: GPL-3.0-only
#include "125a_wav_input.h"
#include <cassert> // deliberately NOT used for acceptance checks in Release
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>
using namespace eii::wav;
using Bytes=std::vector<std::uint8_t>;
void fail(const char* s){std::cerr<<"FAIL "<<s<<"\n";std::exit(1);}
void check(bool b,const char* s){if(!b)fail(s);}
template<typename Fn>void reject(Fn&& f,const char* s){
    try{f();}catch(const std::exception&){return;}fail(s);
}
void put16(Bytes& b,std::uint16_t n){b.push_back(n&255);b.push_back(n>>8);}
void put32(Bytes& b,std::uint32_t n){put16(b,n&65535);put16(b,n>>16);}
void chunk(Bytes& b,const char* id,const Bytes& data){
    b.insert(b.end(),id,id+4);put32(b,std::uint32_t(data.size()));
    b.insert(b.end(),data.begin(),data.end());if(data.size()&1)b.push_back(0);
}
Bytes file(std::uint16_t tag,std::uint16_t bits,std::uint16_t channels,
           std::uint32_t rate,const Bytes& frames){
    Bytes b={'R','I','F','F',0,0,0,0,'W','A','V','E'};
    chunk(b,"JUNK",{7}); // odd padded foreign chunk
    Bytes fmt;put16(fmt,tag);put16(fmt,channels);put32(fmt,rate);
    put32(fmt,rate*channels*(bits/8));put16(fmt,channels*(bits/8));put16(fmt,bits);
    chunk(b,"fmt ",fmt);chunk(b,"data",frames);
    const auto n=std::uint32_t(b.size()-8);
    for(unsigned i=0;i<4;++i)b[4+i]=std::uint8_t(n>>(i*8));
    return b;
}
void near(double actual,double expected,double eps,const char* msg) {
    if(std::abs(actual-expected)>eps)fail(msg);
}
int main(){
    // Mono PCM16: exact positive/negative and midpoint values, with
    // forward machine-tick timing. idle() must NOT consume/start the WAV.
    Bytes pcm;put16(pcm,0x2000);put16(pcm,0x6000);put16(pcm,0x8000);
    const auto decoded=decode(file(1,16,1,48000,pcm));
    check(decoded.channels==1&&decoded.rate==48000&&decoded.mono.size()==3,"PCM16 metadata");
    near(decoded.mono[0],.25,1e-9,"PCM16 first");
    near(decoded.mono[1],.75,1e-9,"PCM16 second");
    near(decoded.mono[2],-1,1e-9,"PCM16 negative rail");
    Source src(decoded);
    src.idle(800000);check(!src.started(),"idle must not start WAV");
    near(src.volts(1000000),.25,1e-9,"first real SAMPLE tick starts input");
    near(src.volts(1000000+std::uint64_t(4000000/48000)),
         .25+(.75-.25)*(double(4000000/48000)*48000/4000000),1e-6,
         "machine-tick interpolation");
    near(src.volts(1000000+4000000),0,1e-9,"post-wave silence");
    // Stereo PCM24 downmix: both channels independently parsed and averaged.
    Bytes stereo24={0xff,0xff,0x7f,0x00,0x00,0x80};
    const auto d24=decode(file(1,24,2,44100,stereo24));
    check(d24.channels==2&&d24.mono.size()==1,"PCM24 stereo metadata");
    near(d24.mono[0],-1.0/16777216.0,1e-8,"PCM24 signed stereo average");
    // PCM8 unsigned maps midpoint to silence.
    const auto d8=decode(file(1,8,1,48000,{0,128,255}));
    near(d8.mono[0],-1,1e-9,"PCM8 min");
    near(d8.mono[1],0,1e-9,"PCM8 zero");
    // IEEE float32: finite, full-scale, no hidden normalization.
    Bytes f;put32(f,std::bit_cast<std::uint32_t>(.5f));
    const auto df=decode(file(3,32,1,96000,f));
    near(df.mono.at(0),.5,1e-9,"float32 amplitude");
    put32(f,0x7fc00000u);
    reject([&]{decode(file(3,32,1,96000,f));},"NaN float must be rejected");
    Bytes hot;put32(hot,std::bit_cast<std::uint32_t>(1.5f));
    reject([&]{decode(file(3,32,1,96000,hot));},"float >0 dBFS must be rejected");
    // 32-bit integer and malformed block geometry.
    Bytes pcm32;put32(pcm32,0x7fffffff);
    near(decode(file(1,32,1,48000,pcm32)).mono[0],1,1e-6,"PCM32");
    Bytes torn=file(1,16,1,48000,pcm);torn.pop_back();
    reject([&]{decode(torn);},"truncated chunk/padding");
    Bytes wrong=file(1,16,1,48000,pcm);wrong[32]=3; // blockAlign in fmt is at offset 42 for JUNK
    wrong[42]=3;reject([&]{decode(wrong);},"incorrect WAV block alignment");
    reject([&]{decode(file(1,16,3,48000,pcm));},"unsupported >2 channels");
    // Real filesystem load occurs off the emulated/audio thread.
    const auto path=std::filesystem::temp_directory_path()/"125a-wav-input-test.wav";
    const auto original=file(1,16,1,48000,pcm);
    {std::ofstream out(path,std::ios::binary|std::ios::trunc);
     out.write(reinterpret_cast<const char*>(original.data()),std::streamsize(original.size()));}
    const auto loaded=load(path);
    check(loaded.mono.size()==3&&loaded.rate==48000,"filesystem load");
    std::filesystem::remove(path);
    reject([&]{load(path);},"missing WAV must reject");
    std::cout<<"125A WAV input decoder/SAR feed contract: PASS\n";
}
