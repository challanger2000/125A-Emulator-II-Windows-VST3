// SPDX-License-Identifier: GPL-3.0-only
#include "125a_media_safety.h"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <vector>
using namespace eii;
static void check(bool b,const char* label){if(!b){std::cerr<<"FAIL "<<label<<"\n";std::exit(1);}}
int main(){
    check(portable::canonicalEiiBankSize(485887),"original bank 485887 permitted");
    check(!portable::canonicalEiiBankSize(0),"empty bank rejected");
    check(!portable::canonicalEiiBankSize(1),"single-byte partial bank rejected");
    check(!portable::canonicalEiiBankSize(485886),"one-byte truncated bank rejected");
    check(!portable::canonicalEiiBankSize(494592),"extended/padded bank rejected");
    constexpr std::size_t hddBytes=22597632;
    std::vector<std::uint8_t> blank(hddBytes);
    auto s=portable::inspectHdd(blank);
    check(s.capacity==46&&s.available==0&&s.unformatted,"20MB raw HDD requires original firmware format");
    for(unsigned i=0;i<s.capacity;++i){
        const auto at=bank::hddDirBase+bank::hddDirStride*i;
        std::copy(bank::nullName.begin(),bank::nullName.end(),blank.begin()+at);
    }
    s=portable::inspectHdd(blank);
    check(s.capacity==46&&s.available==46&&!s.unformatted,"formatted directory exposes 46 free slots");
    const auto at=bank::hddDirBase;
    const std::array<std::uint8_t,12> choir={'C','H','O','I','R',' ',' ',' ',' ',' ',' ',' '};
    std::copy(choir.begin(),choir.end(),blank.begin()+at);
    s=portable::inspectHdd(blank);
    check(s.capacity==46&&s.available==45&&!s.unformatted,"occupied bank not counted as free");
    for(unsigned i=1;i<46;++i){
        const auto next=bank::hddDirBase+bank::hddDirStride*i;
        std::copy(choir.begin(),choir.end(),blank.begin()+next);
    }
    s=portable::inspectHdd(blank);
    check(s.capacity==46&&s.available==0&&!s.unformatted,"full formatted HDD not mistaken for unformatted");
    std::cout<<"P012 strict .EII and original HDD directory validation: PASS\n";
}
