// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// WAV -> original EII analog SAMPLE input (+INPUT.V).
// Decoding/file access: control thread only. volts(): machine owner thread only.
// This is an input source, NOT a shortcut that writes sample DRAM or fabricates a preset.
#include "sample_input_analog.h"
#include <algorithm>
#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace eii::wav {
inline constexpr std::size_t maxWavBytes = 64u * 1024u * 1024u;
inline constexpr double machineTicksPerSecond = 4000000.0;

struct Wav {
    std::uint32_t rate = 0;
    std::uint16_t channels = 0;
    std::vector<float> mono;
};

inline std::uint16_t u16(const std::vector<std::uint8_t>& b,std::size_t n) {
    if(n>b.size()||b.size()-n<2)throw std::runtime_error("Truncated WAV field");
    return std::uint16_t(std::uint16_t(b[n])|(std::uint16_t(b[n+1])<<8));
}
inline std::uint32_t u32(const std::vector<std::uint8_t>& b,std::size_t n) {
    if(n>b.size()||b.size()-n<4)throw std::runtime_error("Truncated WAV field");
    return std::uint32_t(b[n])|(std::uint32_t(b[n+1])<<8)|
           (std::uint32_t(b[n+2])<<16)|(std::uint32_t(b[n+3])<<24);
}
inline bool fourcc(const std::vector<std::uint8_t>& b,std::size_t at,const char* name) {
    return at<=b.size()&&b.size()-at>=4&&b[at]==std::uint8_t(name[0])&&
           b[at+1]==std::uint8_t(name[1])&&b[at+2]==std::uint8_t(name[2])&&
           b[at+3]==std::uint8_t(name[3]);
}

inline Wav decode(const std::vector<std::uint8_t>& b) {
    if(b.size()<44||b.size()>maxWavBytes||!fourcc(b,0,"RIFF")||!fourcc(b,8,"WAVE"))
        throw std::runtime_error("Only bounded RIFF/WAVE files are supported");
    const auto riffSize=u32(b,4);
    if(riffSize<36||std::uint64_t(riffSize)+8>b.size())
        throw std::runtime_error("Truncated RIFF payload");
    const std::size_t end=std::size_t(riffSize)+8;
    std::size_t fmtAt=0,fmtLen=0,dataAt=0,dataLen=0;
    bool haveFmt=false,haveData=false;
    for(std::size_t p=12;p<end;) {
        if(end-p<8)throw std::runtime_error("Truncated WAV chunk header");
        const auto len=std::size_t(u32(b,p+4));
        if(len>end-p-8)throw std::runtime_error("WAV chunk extends past RIFF");
        if(fourcc(b,p,"fmt ")&&!haveFmt){fmtAt=p+8;fmtLen=len;haveFmt=true;}
        if(fourcc(b,p,"data")&&!haveData){dataAt=p+8;dataLen=len;haveData=true;}
        const auto padded=len+(len&1u);
        if(padded>end-p-8)throw std::runtime_error("Truncated WAV chunk padding");
        p+=8+padded;
    }
    if(!haveFmt||!haveData||fmtLen<16)throw std::runtime_error("Missing WAV fmt/data");
    std::uint16_t format=u16(b,fmtAt),channels=u16(b,fmtAt+2);
    const auto rate=u32(b,fmtAt+4),bytesPerSecond=u32(b,fmtAt+8);
    const auto blockAlign=u16(b,fmtAt+12),bits=u16(b,fmtAt+14);
    if(format==0xfffe) {
        // WAVE_FORMAT_EXTENSIBLE: accept only standard PCM/IEEE_FLOAT GUIDs.
        if(fmtLen<40||u16(b,fmtAt+16)<22||u16(b,fmtAt+18)!=bits)
            throw std::runtime_error("Unsupported WAV extensible format");
        static constexpr std::uint8_t guidTail[12]={0,0,0x10,0,0x80,0,0,0xaa,0,0x38,0x9b,0x71};
        for(unsigned j=0;j<12;++j)if(b[fmtAt+28+j]!=guidTail[j])
            throw std::runtime_error("Unsupported WAV subformat GUID");
        const auto sub=u32(b,fmtAt+24);
        if(sub!=1&&sub!=3)throw std::runtime_error("Unsupported WAV subformat");
        format=std::uint16_t(sub);
    }
    const bool integer=format==1&& (bits==8||bits==16||bits==24||bits==32);
    const bool floating=format==3&&bits==32;
    if((!integer&&!floating)||channels<1||channels>2||rate<8000||rate>384000)
        throw std::runtime_error("Unsupported WAV encoding/channels/rate");
    const std::uint64_t bytesPerFrame=std::uint64_t(channels)*(bits/8);
    if(blockAlign!=bytesPerFrame||bytesPerSecond!=std::uint64_t(rate)*bytesPerFrame||
       dataLen==0||dataLen%blockAlign!=0)
        throw std::runtime_error("Invalid WAV frame alignment");
    const auto frames=dataLen/blockAlign;
    if(frames>maxWavBytes/sizeof(float))throw std::runtime_error("WAV has too many frames");
    Wav result;result.rate=rate;result.channels=channels;result.mono.reserve(frames);
    const auto perSample=std::size_t(bits/8);
    for(std::size_t i=0;i<frames;++i){
        double mix=0;
        for(std::size_t ch=0;ch<channels;++ch){
            const auto at=dataAt+i*blockAlign+ch*perSample;
            double v=0;
            if(floating) {
                v=std::bit_cast<float>(u32(b,at));
                if(!std::isfinite(v)||v<-1.0||v>1.0)
                    throw std::runtime_error("Nonfinite or above-full-scale float WAV");
            }else if(bits==8)v=(double(b[at])-128.0)/128.0;
            else if(bits==16)v=double(std::int16_t(u16(b,at)))/32768.0;
            else if(bits==24){
                std::int32_t n=std::int32_t(b[at])|(std::int32_t(b[at+1])<<8)|
                               (std::int32_t(b[at+2])<<16);
                if(n&0x800000)n-=0x1000000;
                v=double(n)/8388608.0;
            }else v=double(std::int32_t(u32(b,at)))/2147483648.0;
            mix+=v;
        }
        result.mono.push_back(float(mix/double(channels)));
    }
    return result;
}
inline Wav load(const std::filesystem::path& path) {
    std::error_code ec;const auto length=std::filesystem::file_size(path,ec);
    if(ec||length<44||length>maxWavBytes)throw std::runtime_error("WAV missing or exceeds 64 MiB input limit");
    std::ifstream in(path,std::ios::binary);
    if(!in)throw std::runtime_error("Unable to open WAV");
    std::vector<std::uint8_t> bytes(std::size_t(length),0);
    if(!in.read(reinterpret_cast<char*>(bytes.data()),std::streamsize(bytes.size())))
        throw std::runtime_error("Incomplete WAV read");
    return decode(bytes);
}

// On the FIRST analog sample request (firmware IMODE), begin playback at
// emulated time zero. idle() deliberately does not start playback. The
// original SAR/anti-alias/ADC path remains solely responsible for recording.
class Source final:public analog::SampleInputSource {
public:
    explicit Source(Wav wav):wave_(std::move(wav)) {
        if(wave_.mono.empty()||wave_.rate==0)throw std::invalid_argument("Empty WAV input");
    }
    double volts(std::uint64_t tick,double fraction=0)noexcept override {
        if(!started_){startTick_=tick;started_=true;}
        if(tick<startTick_)return 0;
        const double position=(double(tick-startTick_)+fraction)*double(wave_.rate)/machineTicksPerSecond;
        if(!std::isfinite(position)||position<0||position>=double(wave_.mono.size()))return 0;
        const auto index=std::size_t(position),next=std::min(index+1,wave_.mono.size()-1);
        const double frac=position-double(index);
        return double(wave_.mono[index])+(double(wave_.mono[next])-wave_.mono[index])*frac;
    }
    void idle(std::uint64_t)noexcept override {} // no trigger before firmware SAMPLE
    bool started()const noexcept{return started_;}
    std::size_t frames()const noexcept{return wave_.mono.size();}
    std::uint32_t rate()const noexcept{return wave_.rate;}
private:
    Wav wave_;
    std::uint64_t startTick_=0;
    bool started_=false;
};
inline std::shared_ptr<analog::SampleInputSource> loadSource(const std::filesystem::path& path) {
    return std::make_shared<Source>(load(path));
}
} // namespace eii::wav
