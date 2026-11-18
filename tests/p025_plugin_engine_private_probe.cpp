// SPDX-License-Identifier: GPL-3.0-only
// P025: complete REAL VST3 machine-owner C++ Engine integration test.
// This includes P008..P024 source-pinned overlays, NOT just the original
// Machine::run() core. Public mode creates no proprietary firmware.
// Optional local --private uses owner's existing ROM/floppy ONLY on device;
// never upload media or original audio to GitHub.
#include "vst3/plugin_engine.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using Clock=std::chrono::steady_clock;
using namespace std::chrono_literals;

namespace {
void need(bool b,const std::string& what) {
    if(!b)throw std::runtime_error("P025 "+what);
}
std::string label(eii::vst::EngineStatus const& s) {
    return std::string(eii::portable::bootStageName(s.boot.stage))+
        " elapsed="+std::to_string(s.boot.wallMs)+
        " virtual_ticks="+std::to_string(s.boot.virtualTicks)+
        " bootMidiDropped="+std::to_string(s.bootMidiDiscarded)+
        " cpu_ticks="+std::to_string(s.panel.ticks)+
        " startup="+s.panel.startup+" error="+s.panel.error;
}
void writeBinary(const std::filesystem::path& p,unsigned count,std::uint8_t fill) {
    std::ofstream out(p,std::ios::binary);
    if(!out)throw std::runtime_error("Failed to open synthetic private-free ROM fixture");
    std::vector<char> b(count,char(fill));
    out.write(b.data(),std::streamsize(b.size()));
    if(!out)throw std::runtime_error("Failed to write synthetic ROM fixture");
}
std::filesystem::path makeSyntheticRoms() {
    const auto path=std::filesystem::temp_directory_path()/
       ("eii_p025_synthetic_"+std::to_string(
           std::chrono::duration_cast<std::chrono::nanoseconds>(
              Clock::now().time_since_epoch()).count()));
    std::filesystem::create_directories(path);
    // Intentionally invalid Z80 NOP ROMs exercise original bus-fault handling.
    // This is a NEGATIVE test only; real 4MHz freewheel needs original ROM.
    writeBinary(path/"main.bin",8192,0x00);
    writeBinary(path/"scanner.bin",8192,0x00);
    writeBinary(path/"ic135.bin",512,0x00);
    writeBinary(path/"ic137.bin",512,0x00);
    return path;
}
void assertSilentDuringBoot(eii::vst::PluginEngine& e) {
    constexpr int N=512;
    std::array<float,N> left{},right{};
    for(auto& v:left)v=55.f;
    for(auto& v:right)v=-88.f;
    std::array<std::array<float,N>,8> ch{};
    std::array<float*,8> channel{};
    for(unsigned i=0;i<8;++i){
        ch[i].fill(99.f);
        channel[i]=ch[i].data();
    }
    e.render(left.data(),right.data(),N,false,channel.data());
    for(int i=0;i<N;++i){
        need(left[i]==0&&right[i]==0,"boot render main stereo not silent");
        for(unsigned j=0;j<8;++j)
            need(ch[j][i]==0,"boot render aux output not silent");
    }
}
void synthetic() {
    const auto fixture=makeSyntheticRoms();
    {
        eii::vst::PluginEngine engine;
        engine.setupProcessing(48000,512);
        engine.activate();
        eii::vst::PluginSettings settings;
        settings.romFolder=fixture;
        settings.audioMode=eii::analog::RuntimeAudioMode::BasicVoice;
        engine.boot(settings,true);
        auto start=Clock::now();
        eii::vst::EngineStatus s;
        do {
            std::this_thread::sleep_for(30ms);
            s=engine.status();
            if(s.halted)break;
        } while(Clock::now()-start<4s);
        std::cout<<"SYNTHETIC_INVALID_ROM "<<label(s)<<"\n";
        // A no-op ROM is NOT a valid E-mu board configuration: its RFD bus
        // drivers conflict at clock tick 1 under the real controller model.
        // This is a negative test, NOT proof of a 4MHz autonomous boot.
        need(s.halted,"invalid synthetic ROM must fail closed");
        need(s.boot.stage==eii::portable::BootStage::Failed,
             "invalid ROM must never claim playable original firmware Pxx");
        need(s.panel.error.find("conflicting RFD bus drivers")!=std::string::npos,
             "retain original hardware bus fault rather than masking it with a generic timeout");
        // Even when guest hardware halts, DAW buses must be fully silent
        // and the plugin must not crash or leave uninitialized buffers.
        assertSilentDuringBoot(engine);
        std::cout<<"P025 SYNTHETIC INVALID ORIGINAL ROM HARDWARE-FAULT DIAGNOSTIC "
                 <<"AND 10-BUS SILENCE: PASS\n";
    }
    std::filesystem::remove_all(fixture);
}
void privateOriginal(const std::filesystem::path& rom,const std::filesystem::path& floppy){
    const auto started=Clock::now();
    eii::vst::PluginEngine e;
    e.setupProcessing(48000,512);
    e.activate();
    eii::vst::PluginSettings settings;
    settings.romFolder=rom;
    settings.floppy=floppy;
    settings.audioMode=eii::analog::RuntimeAudioMode::BasicVoice;
    settings.directImageWrites=false;
    settings.memory1mb=false;
    e.boot(settings,true);
    // ZERO DAW process() calls while original firmware boots. Only the
    // product's real, patched PluginEngine owner thread advances hardware.
    eii::vst::EngineStatus s;
    bool ready=false;
    while(Clock::now()-started<240s) {
        std::this_thread::sleep_for(75ms);
        s=e.status();
        if(s.boot.complete && s.boot.stage==eii::portable::BootStage::Ready &&
           !s.autonomousBoot){ready=true;break;}
        if(s.halted)break;
    }
    std::cout<<"PRIVATE_ORIGINAL_PLUGIN_BOOT "<<label(s)
             <<" actual_wall="<<std::chrono::duration<double>(Clock::now()-started).count()
             <<"s\n";
    need(ready,"actual plugin engine failed private original-ROM Pxx+MIDI-ready autonomous boot");
    need(s.boot.virtualTicks>10000000,"original firmware clock ran too few cycles");

    std::array<float,512> l{},r{};
    double energy=0,peak=0;
    std::uint64_t active=0;
    const auto noteOn=std::array<std::uint8_t,3>{0x90,60,100};
    const auto noteOff=std::array<std::uint8_t,3>{0x80,60,0};
    e.queueMidi(0,noteOn.data(),3);
    for(int i=0;i<330;++i) {
        if(i==200)e.queueMidi(0,noteOff.data(),3);
        e.render(l.data(),r.data(),512,true);
        for(int j=0;j<512;++j) {
            const auto a=std::max(std::abs(l[j]),std::abs(r[j]));
            if(a>1.e-8f)++active;
            peak=std::max(peak,double(a));
            energy+=double(l[j])*l[j]+double(r[j])*r[j];
        }
    }
    s=e.status();
    std::cout<<"PRIVATE_ORIGINAL_PLUGIN_AUDIO frames="<<330*512
             <<" nonzero="<<active<<" peak="<<std::setprecision(12)<<peak
             <<" energy="<<energy
             <<" callbacks="<<s.callbacks<<" underruns="<<s.underruns
             <<" host_lag="<<s.ownerLagMs
             <<" midi_dropped_during_boot="<<s.bootMidiDiscarded
             <<" total_wall="<<std::chrono::duration<double>(Clock::now()-started).count()
             <<"s\n";
    need(active>2000&&peak>0.001,
         "actual plugin-engine DAW audio handoff produced no genuine original Choir sound");
    need(s.halted==false,"original machine halted during host audio/MIDI playback");
    std::cout<<"P025 PRIVATE ORIGINAL ROM 4MHZ -> REAL PATCHED VST3 ENGINE -> "
             <<"DAW PCM AUDIO HANDOFF: PASS\n";

    // P027: production reload into THE SAME PluginEngine after the first
    // actual original Choir has played. No DAW audio callbacks while the
    // original machine starts again. This catches stale host audio rings,
    // MIDI events, guest/host clock anchors and preboot silence regressions.
    const double firstPeak=peak,firstEnergy=energy;
    const auto rebootStart=Clock::now();
    e.boot(settings,true);
    bool enteredReboot=false;
    while(Clock::now()-rebootStart<15s){
        std::this_thread::sleep_for(50ms);
        s=e.status();
        if(s.autonomousBoot){enteredReboot=true;break;}
        if(s.halted)break;
    }
    std::cout<<"P027_REBOOT_STARTED "<<label(s)
             <<" wall="<<std::chrono::duration<double>(Clock::now()-rebootStart).count()
             <<"s\n";
    need(enteredReboot,"second original firmware boot never entered autonomous mode");
    assertSilentDuringBoot(e); // previous original note must not leak
    const std::array<std::uint8_t,3> ignoredPreboot{0x90,62,127};
    e.queueMidi(0,ignoredPreboot.data(),3); // must be discarded while ROM boots
    bool secondReady=false;
    while(Clock::now()-rebootStart<240s){
        std::this_thread::sleep_for(75ms);
        s=e.status();
        if(s.boot.complete&&s.boot.stage==eii::portable::BootStage::Ready&&
           !s.autonomousBoot){secondReady=true;break;}
        if(s.halted)break;
    }
    std::cout<<"P027_SECOND_ORIGINAL_BOOT "<<label(s)
             <<" wall="<<std::chrono::duration<double>(Clock::now()-rebootStart).count()
             <<"s\n";
    need(secondReady,"second full original ROM startup failed to reach Pxx+MIDI");
    need(s.bootMidiDiscarded>=1,
         "MIDI sent during second boot must not become a stuck new performance note");
    need(s.boot.virtualTicks>10000000,
         "second original ROM restart did not execute actual full 4MHz firmware");

    std::uint64_t activeAgain=0;
    double peakAgain=0,energyAgain=0;
    e.queueMidi(0,noteOn.data(),3);
    for(int i=0;i<330;++i){
        if(i==200)e.queueMidi(0,noteOff.data(),3);
        e.render(l.data(),r.data(),512,true);
        for(int j=0;j<512;++j){
            const auto a=std::max(std::abs(l[j]),std::abs(r[j]));
            if(a>1.e-8f)++activeAgain;
            peakAgain=std::max(peakAgain,double(a));
            energyAgain+=double(l[j])*l[j]+double(r[j])*r[j];
        }
    }
    s=e.status();
    std::cout<<"P027_SECOND_ORIGINAL_AUDIO nonzero="<<activeAgain
             <<" peak="<<std::setprecision(12)<<peakAgain
             <<" energy="<<energyAgain
             <<" first_peak="<<firstPeak<<" first_energy="<<firstEnergy
             <<" total_callbacks="<<s.callbacks
             <<" total_underruns="<<s.underruns
             <<" dropped_preboot_midi="<<s.bootMidiDiscarded
             <<"\n";
    need(activeAgain>2000&&peakAgain>0.001,
         "audio after second original firmware boot vanished or stale buffer poisoned playback");
    need(s.underruns==0,"second actual original-ROM offline DAW output underrun");
    need(!s.halted,"machine halted during second audio playback");
    need(energyAgain>firstEnergy*0.2&&energyAgain<firstEnergy*5,
         "second original instrument sound energy differs wildly from same preset");
    std::cout<<"P027 SAME VST3 PLUGINENGINE FULL ORIGINAL ROM/CHOIR REBOOT + "
             <<"MIDI AFTER PXX + DAW PCM AUDIO RECOVERY: PASS\n";
}
}
int main(int argc,char** argv){
    try{
        if(argc==4&&std::string_view(argv[1])=="--private-only"){
            privateOriginal(argv[2],argv[3]);
            return 0;
        }
        synthetic();
        if(argc==3)privateOriginal(argv[1],argv[2]);
        else if(argc!=1){
            std::cerr<<"usage: p025_plugin_engine_private_probe [local-rom-folder local-original-floppy] or --private-only rom floppy\n";
            return 2;
        }
        return 0;
    }catch(const std::exception& e){
        std::cerr<<"P025 FAIL "<<e.what()<<"\n";
        return 1;
    }
}
