// SPDX-License-Identifier: GPL-3.0-only
#include "125a_portable_state.h"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using namespace eii::portable;
void need(bool good,const char* what){if(!good){std::cerr<<"FAIL "<<what<<"\n";std::exit(1);}}
template<class F> void rejects(F&& f,const char* name){
    try{f();}catch(const std::exception&){return;}need(false,name);
}
int main(){
    std::string settings="EIIVST3 1\nrom=C:/ROMS\nfloppy=C:/DISKS\nmodel=4\n";
    std::vector<std::uint8_t> bank(bankBytes);
    for(std::size_t i=0;i<bank.size();++i)bank[i]=std::uint8_t((i*19+(i>>7)+17)&255);
    need(encode(settings)==settings,"unmodified legacy state");
    const auto old=decode(settings);
    need(old.settings==settings&&!old.hasBank(),"parse old plain state");
    const auto combined=encode(settings,bank);
    need(combined.size()==headerSize+settings.size()+bankBytes,"raw binary compact envelope");
    need(combined.size()<maxStateBytes,"fits VST3 read bound");
    const auto rebuilt=decode(combined);
    need(rebuilt.settings==settings&&rebuilt.bank==bank,"exact full disk round trip");
    auto broken=combined;broken[broken.size()-1]^=1;
    rejects([&]{decode(broken);},"payload corruption");
    broken=combined;broken[headerSize+13]^=1;
    rejects([&]{decode(broken);},"settings corruption");
    broken=combined;broken[magic.size()+4]^=1;
    rejects([&]{decode(broken);},"non-exact media length");
    broken=combined;broken.pop_back();
    rejects([&]{decode(broken);},"truncated complete disk");
    broken=combined;broken.push_back('\0');
    rejects([&]{decode(broken);},"trailing garbage");
    rejects([&]{decode("unknown product state");},"unknown state");
    rejects([&]{encode(settings,std::span<const std::uint8_t>(bank.data(),bank.size()-1));},"partial image");
    std::string wrong="OTHER-VST3 1\n";
    rejects([&]{encode(wrong,bank);},"foreign settings");
    auto b2=bank;b2[40000]^=0x7f;
    need(decode(encode(settings,b2)).bank==b2,"distinct independent saved banks");
    for(std::size_t n=0;n<headerSize+24;++n){
        rejects([&]{decode(std::string_view(combined).substr(0,n));},"all short prefixes rejected");
    }
    std::cout<<"125A P004 full 573440-byte performance-media project-state codec: PASS, bytes "<<combined.size()<<"\n";
}
