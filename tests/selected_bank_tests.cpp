// SPDX-License-Identifier: GPL-3.0-only
#include "125a_selected_bank.h"
#include <cstdlib>
#include <iostream>
#include <vector>
using namespace eii::portable;
static void need(bool value,const char* message){
    if(!value){std::cerr<<"FAIL "<<message<<"\n";std::exit(1);}
}
int main(){
    std::vector<std::uint8_t> image(bankBytes);
    for(std::size_t i=0;i<image.size();++i)image[i]=std::uint8_t((i*37+i/29+11)&255);
    const auto original=image;
    auto bank=cloneSelectedBank(image);
    need(bool(bank),"selection created project bank");
    need(bank->size()==bankBytes,"full bank length");
    for(std::size_t i=0;i<bankDataOffset;++i)
        need((*bank)[i]==0,"zero original OS prefix");
    for(std::size_t i=bankDataOffset;i<bankBytes;++i)
        need((*bank)[i]==original[i],"sample/program region bit exact");
    // Eject / reuse / mutation of the media cannot mutate the committed bank.
    image.assign(bankBytes,0);
    need((*bank)[bankDataOffset+1234]==original[bankDataOffset+1234],
         "project bank survives media replacement");
    auto second=cloneSelectedBank(image);
    need(second!=bank,"independent immutable bank storage");
    need((*second)[bankDataOffset+1234]!=(*bank)[bankDataOffset+1234],
         "changing selection does not corrupt old snapshot");
    const auto song=encode("EIIVST3 1\nmodel=1\n",*bank);
    need(decode(song).bank==*bank,"bank survives VST3 project codec round trip");
    bool rejected=false;
    try{(void)cloneSelectedBank(std::span<const std::uint8_t>(original.data(),original.size()-1));}
    catch(const std::exception&){rejected=true;}
    need(rejected,"partial media fails closed");
    rejected=false;
    try{(void)cloneSelectedBank(std::span<const std::uint8_t>{});}
    catch(const std::exception&){rejected=true;}
    need(rejected,"empty media fails closed");
    std::cout<<"P010 selected bank / Eject / immutable project state: PASS\n";
}
