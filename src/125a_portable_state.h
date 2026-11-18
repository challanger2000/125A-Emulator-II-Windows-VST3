// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Portable original EII performance bank inside VST3 IBStream project state.
// Binary envelope: magic(16), settingsLen(4), bankLen(4), fnv1a64(8),
// original EIIVST3 settings bytes, complete 573440-byte EMUIIFD bank image.
// No sample RAM shortcuts and no cryptographic authenticity claim.
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
namespace eii::portable {
inline constexpr std::size_t bankBytes=573440;
inline constexpr std::size_t maxSettingsBytes=128u*1024u;
inline constexpr std::size_t maxStateBytes=1024u*1024u;
inline constexpr std::array<char,16> magic={'1','2','5','A','E','I','I','B','A','N','K','0','0','1','\r','\n'};
inline constexpr std::string_view oldMagic="EIIVST3 1\n";
inline constexpr std::size_t headerSize=magic.size()+4+4+8;
struct ProjectState {
    std::string settings;
    std::vector<std::uint8_t> bank;
    bool hasBank()const noexcept{return !bank.empty();}
};
inline void write32(std::string& dest,std::uint32_t x){
    for(unsigned i=0;i<4;++i)dest.push_back(char((x>>(8*i))&255));
}
inline void write64(std::string& dest,std::uint64_t x){
    for(unsigned i=0;i<8;++i)dest.push_back(char((x>>(8*i))&255));
}
inline std::uint32_t read32(std::string_view s,std::size_t n){
    if(n>s.size()||s.size()-n<4)throw std::runtime_error("Truncated EII bank length");
    std::uint32_t r=0;for(unsigned i=0;i<4;++i)r|=std::uint32_t(std::uint8_t(s[n+i]))<<(8*i);
    return r;
}
inline std::uint64_t read64(std::string_view s,std::size_t n){
    if(n>s.size()||s.size()-n<8)throw std::runtime_error("Truncated EII bank checksum");
    std::uint64_t r=0;for(unsigned i=0;i<8;++i)r|=std::uint64_t(std::uint8_t(s[n+i]))<<(8*i);
    return r;
}
inline std::uint64_t hash(std::string_view s)noexcept {
    std::uint64_t h=14695981039346656037ull;
    for(const unsigned char c:s){h^=c;h*=1099511628211ull;}
    return h;
}
inline void validateSettings(std::string_view s){
    if(s.size()>maxSettingsBytes||s.substr(0,oldMagic.size())!=oldMagic)
        throw std::runtime_error("Foreign or oversized EIIVST3 project settings");
}
inline std::string encode(std::string_view settings,std::span<const std::uint8_t> bank={}){
    validateSettings(settings);
    if(bank.empty())return std::string(settings); // old projects stay byte-for-byte identical
    if(bank.size()!=bankBytes)throw std::runtime_error("EII embedded disk must be exactly 573440 bytes");
    if(headerSize+settings.size()+bank.size()>maxStateBytes)
        throw std::runtime_error("Embedded bank exceeds VST3 1-MiB input bound");
    std::string result;result.reserve(headerSize+settings.size()+bank.size());
    result.append(magic.data(),magic.size());
    write32(result,std::uint32_t(settings.size()));
    write32(result,std::uint32_t(bank.size()));
    const auto combined=std::string(settings)+std::string(reinterpret_cast<const char*>(bank.data()),bank.size());
    write64(result,hash(combined));
    result.append(settings.data(),settings.size());
    result.append(reinterpret_cast<const char*>(bank.data()),bank.size());
    return result;
}
inline ProjectState decode(std::string_view data){
    if(data.size()>maxStateBytes)throw std::runtime_error("Oversized EII project state");
    if(data.substr(0,oldMagic.size())==oldMagic){
        validateSettings(data);return {std::string(data),{}};
    }
    if(data.size()<headerSize||data.substr(0,magic.size())!=std::string_view(magic.data(),magic.size()))
        throw std::runtime_error("Unknown EII project state envelope");
    const auto settingsLen=std::size_t(read32(data,magic.size()));
    const auto mediaLen=std::size_t(read32(data,magic.size()+4));
    const auto storedHash=read64(data,magic.size()+8);
    if(settingsLen>maxSettingsBytes||mediaLen!=bankBytes||
       settingsLen>data.size()-headerSize||mediaLen!=data.size()-headerSize-settingsLen)
        throw std::runtime_error("Malformed embedded EII disk boundaries");
    const auto body=data.substr(headerSize);
    if(hash(body)!=storedHash)throw std::runtime_error("Embedded EII bank checksum mismatch");
    const auto settings=body.substr(0,settingsLen);
    validateSettings(settings);
    const auto media=body.substr(settingsLen);
    std::vector<std::uint8_t> bank;
    bank.reserve(bankBytes);
    for(const auto c:media)bank.push_back(std::uint8_t(c));
    return {std::string(settings),std::move(bank)};
}
} // namespace eii::portable
