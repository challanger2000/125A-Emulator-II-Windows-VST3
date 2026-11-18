// SPDX-License-Identifier: GPL-3.0-only
// Persistent state marker; actual firmware bank capture is not simulated here.
#include "vst3/plugin_state.h"
#include "125a_portable_state.h"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void check(bool b,const char* why){
    if(!b){std::cerr<<"FAIL P014: "<<why<<"\n";std::exit(1);}
}
int main(){
    using namespace eii;
    vst::PluginSettings s;
    const auto original=vst::serializeSettings(s);
    check(original.find("bankpending=")==std::string::npos,
          "committed/legacy project state must remain byte compatible");
    const auto restored=vst::parseSettings(original);
    check(!restored.bankPendingCapture,"legacy projects default to no pending marker");
    s.bankPendingCapture=true;
    const auto flagged=vst::serializeSettings(s);
    const auto where=flagged.find("bankpending=1\n");
    check(where!=std::string::npos && where<flagged.find("calibration:\n"),
          "pending marker precedes calibration section");
    check(vst::parseSettings(flagged).bankPendingCapture,
          "pending marker round trips in project settings");
    check(flagged==vst::serializeSettings(vst::parseSettings(flagged)),
          "pending settings round trip byte for byte");
    std::vector<std::uint8_t> bank(portable::bankBytes);
    for(std::size_t i=portable::bankDataOffset;i<bank.size();++i)
        bank[i]=std::uint8_t((i*13+7)&255);
    const auto project=portable::encode(flagged,bank);
    auto parsed=portable::decode(project);
    check(parsed.hasBank()&&parsed.bank==bank,
          "last committed bank preserved in an autosave during another bank import");
    check(vst::parseSettings(parsed.settings).bankPendingCapture,
          "autosave retains pending-live-bank warning alongside committed snapshot");
    auto corrupt=flagged;
    const auto at=corrupt.find("bankpending=1\n");
    corrupt.replace(at,std::string("bankpending=1").size(),"bankpending=X");
    bool rejected=false;
    try{(void)vst::parseSettings(corrupt);}
    catch(const std::runtime_error&){rejected=true;}
    check(rejected,"reject damaged pending marker rather than clearing warning");
    s.bankPendingCapture=false;
    check(vst::serializeSettings(s)==original,
          "successful subsequent capture clears marker and restores legacy bytes");
    const auto pendingWithoutBank=portable::encode(flagged);
    parsed=portable::decode(pendingWithoutBank);
    check(!parsed.hasBank()&&vst::parseSettings(parsed.settings).bankPendingCapture,
          "empty but pending bank remains an explicit warning after song reopen");
    std::cout<<"P014 Studio One pending-bank persistent-state policy PASS\n";
}
