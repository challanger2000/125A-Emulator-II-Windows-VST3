// SPDX-License-Identifier: GPL-3.0-only
#include "vst3/plugin_state.h"
#include "125a_portable_hdd.h"
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace eii;
static void need(bool x,const char* why){if(!x){std::cerr<<"FAIL P018 "<<why<<"\n";std::exit(1);}}
int main(){
    vst::PluginSettings settings;
    const auto legacy=vst::serializeSettings(settings);
    need(legacy.find("wavmidic3=")==std::string::npos,
         "off by default and byte-for-byte old project encoding");
    const auto old=vst::parseSettings(legacy);
    need(!old.wavC3Keyboard,"legacy project stays original EII MIDI octave");
    settings.wavC3Keyboard=true;
    const auto on=vst::serializeSettings(settings);
    need(on.find("wavmidic3=1\n")!=std::string::npos,
         "explicit C3 mode saved before calibration");
    need(on.find("wavmidic3=1\n")<on.find("calibration:\n"),
         "C3 option saved as project setting, not mutable sampler RAM");
    need(vst::parseSettings(on).wavC3Keyboard,"C3 mode survives project reopen");
    need(vst::serializeSettings(vst::parseSettings(on))==on,
         "C3 project binary-stable roundtrip");
    const auto both=std::vector<std::uint8_t>(portable::bankBytes,0);
    const auto song=portable::encodeProject(on,both);
    const auto reloaded=portable::decodeProject(song);
    need(reloaded.hasBank()&&vst::parseSettings(reloaded.settings).wavC3Keyboard,
         "saved bank and MIDI C3 mapping restored together");
    const auto oldState=portable::encodeProject(legacy,both);
    need(!vst::parseSettings(portable::decodeProject(oldState).settings).wavC3Keyboard,
         "opening older bank state does not auto transpose older sounds");
    auto bad=on;
    const auto i=bad.find("wavmidic3=1\n");
    bad.replace(i,11,"wavmidic3=X");
    bool rejected=false;
    try{(void)vst::parseSettings(bad);}catch(const std::runtime_error&){rejected=true;}
    need(rejected,"foreign/corrupt octave policy rejected");
    settings.wavC3Keyboard=false;
    need(vst::serializeSettings(settings)==legacy,
         "manual return to original firmware mapping removes optional setting");
    std::cout<<"P018 C3 host keyboard setting original VST3 song state PASS\n";
}
