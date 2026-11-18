// SPDX-License-Identifier: GPL-3.0-only
#include "125a_portable_hdd.h"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace eii::portable;
static void check(bool b,const char* s){if(!b){std::cerr<<"FAIL P017: "<<s<<"\n";std::exit(1);}}
template<class F>static void rejects(F f,const char* s){
    try{f();}catch(const std::exception&){return;}
    check(false,s);
}
int main(){
    const std::string settings="EIIVST3 1\nrom=C:/ROMS\nmodel=4\nautoboot=0\n";
    std::vector<std::uint8_t> bank(bankBytes);
    for(std::size_t i=bankDataOffset;i<bank.size();++i)
        bank[i]=std::uint8_t((i*13+7)&255);
    std::vector<std::uint8_t> hdd(22597632,0x6c);
    // 46 potential performance-bank slots. Some represent actual arbitrary
    // sample data so RLE cannot rely exclusively on blank/raw images.
    for(std::size_t k=0;k<46;++k){
        const auto base=k*300000+113;
        for(std::size_t i=0;i<4096;++i)
            hdd[base+i]=std::uint8_t((i*19+k*7+(i>>4))&255);
    }
    const auto old=encode(settings,bank);
    check(encodeProject(settings,bank)==old,"old bank only project bit exact");
    check(encodeProject(settings)==settings,"old legacy settings bit exact");
    const auto newSong=encodeProject(settings,bank,hdd);
    check(newSong.size()<maxProjectStateBytes,"large original HDD fits VST3 bounded project state");
    check(newSong.size()<hdd.size(),"original HDD RLE packs blank/filled sectors");
    const auto result=decodeProject(newSong);
    check(result.settings==settings,"original settings preserved");
    check(result.bank.size()==bankBytes,"original bank dimensions");
    check(std::all_of(result.bank.begin(),result.bank.begin()+bankDataOffset,
                      [](std::uint8_t x){return x==0;}),
          "no proprietary floppy OS in embedded bank");
    check(result.hdd==hdd,"all HDD sectors exact, including synthetic bank sample bytes");
    check(encodeProject(result.settings,result.bank,result.hdd)==newSong,
          "HDD/song state deterministic after decode/reopen/re-save");
    check(decodeProject(old).bank==decode(old).bank,
          "previous P004 full bank states remain decodable");
    check(decodeProject(settings).settings==settings,
          "original VST3 1 state remains readable");
    check(decodeProject(encodeProject(settings,{},hdd)).hdd==hdd,
          "HDD-only song without floppy works");

    auto broken=newSong;broken.back()^=1;
    rejects([&]{decodeProject(broken);},"HDD checksum tampering");
    broken=newSong;broken.pop_back();
    rejects([&]{decodeProject(broken);},"truncated RLE payload");
    broken=newSong;broken.push_back('x');
    rejects([&]{decodeProject(broken);},"trailing HDD bytes");
    broken=newSong;broken[24]=0;
    rejects([&]{decodeProject(broken);},"bogus HDD declared sectors");
    broken=newSong;broken[28]=char(255);
    rejects([&]{decodeProject(broken);},"bogus packed HDD size");
    std::vector<std::uint8_t> truncated(hdd.begin(),hdd.end()-1);
    rejects([&]{encodeProject(settings,{},truncated);},"reject not-sector-aligned original HDD");
    std::vector<std::uint8_t> huge(maxHddBytes+512);
    rejects([&]{encodeProject(settings,{},huge);},"reject oversize original HDD");
    rejects([&]{decompressHdd(std::string_view("\x80",1),512);},"truncated run");
    rejects([&]{decompressHdd(std::string_view("\x7f",1),512);},"truncated literal");
    rejects([&]{decompressHdd(std::string_view("\xff\x00",2),512);},"incomplete decompression");
    // Worst-case noncompressible 1MiB data.
    std::vector<std::uint8_t> noisy(1u<<20);
    std::uint32_t rnd=0x67cba123u;
    for(auto& v:noisy){rnd^=rnd<<13;rnd^=rnd>>17;rnd^=rnd<<5;v=std::uint8_t(rnd);}
    const auto packed=compressHdd(noisy);
    check(decompressHdd(packed,noisy.size())==noisy,
          "full entropy 512-sector image roundtrip");
    std::cout<<"P017 portable original 20 MB HDD + bank + corrupt/legacy state: PASS; packed "<<newSong.size()<<" bytes\n";
}
