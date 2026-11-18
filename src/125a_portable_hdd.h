// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P017: portable original HDD media in the VST3 song. No additional firmware,
// ROM, or third-party compression runtime. The entire HDD is a private
// user-provided image: DO NOT redistribute songs that contain proprietary OS.
#include "125a_portable_state.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace eii::portable {
inline constexpr std::size_t maxHddBytes=32u*1024u*1024u;
inline constexpr std::size_t maxProjectStateBytes=40u*1024u*1024u;
inline constexpr std::array<char,16> hddMagic={
    '1','2','5','A','E','I','I','H','D','D','0','0','0','1','\r','\n'};
inline constexpr std::size_t hddHeaderSize=hddMagic.size()+4+4+4+4+8;

struct PortableProject {
    std::string settings;
    std::vector<std::uint8_t> bank;
    std::vector<std::uint8_t> hdd;
    bool hasBank()const noexcept{return !bank.empty();}
    bool hasHdd()const noexcept{return !hdd.empty();}
};

inline void validateHdd(std::span<const std::uint8_t> hdd){
    if(hdd.empty()||hdd.size()>maxHddBytes||hdd.size()%512)
        throw std::runtime_error("Original EII HDD size must be whole 512-byte sectors, at most 32 MiB");
}
// A strict and bounded byte RLE. 0..127 = (n+1) literals; 128..255 =
// (n+1) copies of the following byte. This also handles HDD formats
// that contain 0x6c filler, 0x00 and random sample payloads.
inline std::string compressHdd(std::span<const std::uint8_t> input){
    validateHdd(input);
    std::string out;
    out.reserve(std::min<std::size_t>(input.size(),4096));
    std::size_t p=0;
    while(p<input.size()){
        std::size_t run=1;
        while(run<128&&p+run<input.size()&&input[p+run]==input[p])++run;
        if(run>=4){
            out.push_back(char(0x80u|std::uint8_t(run-1)));
            out.push_back(char(input[p]));
            p+=run;
            continue;
        }
        const std::size_t start=p;
        p+=run;
        while(p-start<128&&p<input.size()){
            std::size_t r=1;
            while(r<4&&p+r<input.size()&&input[p+r]==input[p])++r;
            if(r>=4)break;
            if(p+r-start>128)break;
            p+=r;
        }
        out.push_back(char(std::uint8_t(p-start-1)));
        out.append(reinterpret_cast<const char*>(input.data()+start),p-start);
    }
    return out;
}
inline std::vector<std::uint8_t> decompressHdd(std::string_view encoded,std::size_t expected){
    if(expected==0||expected>maxHddBytes||expected%512)
        throw std::runtime_error("Invalid original HDD output length in project");
    std::vector<std::uint8_t> out;
    out.reserve(expected);
    for(std::size_t p=0;p<encoded.size();){
        const auto tag=std::uint8_t(encoded[p++]);
        const std::size_t count=(tag&127u)+1u;
        if(count>expected-out.size())throw std::runtime_error("HDD decompression exceeds declared size");
        if(tag&0x80u){
            if(p>=encoded.size())throw std::runtime_error("Truncated repeated HDD byte");
            const auto value=std::uint8_t(encoded[p++]);
            out.insert(out.end(),count,value);
        }else{
            if(count>encoded.size()-p)throw std::runtime_error("Truncated HDD literal");
            for(std::size_t j=0;j<count;++j)out.push_back(std::uint8_t(encoded[p+j]));
            p+=count;
        }
    }
    if(out.size()!=expected)throw std::runtime_error("Incomplete HDD image in song");
    return out;
}
inline std::string encodeProject(std::string_view settings,
                                 std::span<const std::uint8_t> bank={},
                                 std::span<const std::uint8_t> hdd={}){
    if(hdd.empty())return encode(settings,bank); // exact legacy/P004/P010/P014 bytes
    validateSettings(settings);
    validateHdd(hdd);
    if(!bank.empty()&&bank.size()!=bankBytes)
        throw std::runtime_error("HDD song bank must be original 573440-byte image");
    auto packed=compressHdd(hdd);
    std::string body;
    body.reserve(settings.size()+bank.size()+packed.size());
    body.append(settings);
    if(!bank.empty()){
        const auto offset=body.size();
        body.append(reinterpret_cast<const char*>(bank.data()),bank.size());
        std::fill_n(body.begin()+std::ptrdiff_t(offset),bankDataOffset,'\0');
    }
    body.append(packed);
    if(body.size()+hddHeaderSize>maxProjectStateBytes)
        throw std::runtime_error("Original HDD project data exceeds bounded 40-MiB state");
    std::string result;
    result.reserve(hddHeaderSize+body.size());
    result.append(hddMagic.data(),hddMagic.size());
    write32(result,std::uint32_t(settings.size()));
    write32(result,std::uint32_t(bank.size()));
    write32(result,std::uint32_t(hdd.size()));
    write32(result,std::uint32_t(packed.size()));
    write64(result,hash(body));
    result+=body;
    return result;
}
inline PortableProject decodeProject(std::string_view bytes){
    if(bytes.size()>maxProjectStateBytes)
        throw std::runtime_error("VST3 song project state exceeds 40 MiB");
    if(bytes.substr(0,hddMagic.size())!=std::string_view(hddMagic.data(),hddMagic.size())){
        const auto prior=decode(bytes);
        return {prior.settings,prior.bank,{}};
    }
    if(bytes.size()<hddHeaderSize)
        throw std::runtime_error("Truncated HDD song header");
    const auto settingLen=std::size_t(read32(bytes,16));
    const auto bankLen=std::size_t(read32(bytes,20));
    const auto hddLen=std::size_t(read32(bytes,24));
    const auto packedLen=std::size_t(read32(bytes,28));
    const auto expectedHash=read64(bytes,32);
    const auto size=bytes.size()-hddHeaderSize;
    if(settingLen>maxSettingsBytes||(bankLen!=0&&bankLen!=bankBytes)||
       hddLen==0||hddLen>maxHddBytes||hddLen%512||
       packedLen>hddLen+(hddLen+127)/128||
       settingLen>size||bankLen>size-settingLen||
       packedLen!=size-settingLen-bankLen)
        throw std::runtime_error("Invalid original HDD song state boundaries");
    const auto body=bytes.substr(hddHeaderSize);
    if(hash(body)!=expectedHash)
        throw std::runtime_error("Original HDD song checksum mismatch");
    const auto settings=body.substr(0,settingLen);
    validateSettings(settings);
    PortableProject result;
    result.settings=std::string(settings);
    if(bankLen){
        const auto part=body.substr(settingLen,bankLen);
        result.bank.reserve(bankLen);
        for(auto c:part)result.bank.push_back(std::uint8_t(c));
    }
    result.hdd=decompressHdd(body.substr(settingLen+bankLen,packedLen),hddLen);
    return result;
}
} // namespace eii::portable
