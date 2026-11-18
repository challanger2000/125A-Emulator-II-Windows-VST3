// SPDX-License-Identifier: GPL-3.0-only
// P023 private-media bench: built ONLY from public original-machine source.
// Real user's ROM and floppy are supplied locally at execution, NEVER in CI.
// This bench is NOT a second executable shipped with the VST3 product.
#include "machine.h"
#include "floppy_hfe.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Clock=std::chrono::steady_clock;
constexpr std::uint64_t quantum=60000;
constexpr std::uint64_t ticksPerSecond=4000000;
constexpr unsigned maxVirtualSeconds=180;
constexpr unsigned maxWallSeconds=240;

double seconds(Clock::time_point since) {
    return std::chrono::duration<double>(Clock::now()-since).count();
}
bool playable(const eii::Machine& m){
    if(!m.lcd.display)return false;
    const auto line=m.lcd.line(0);
    return line.size()>=3&&line[0]=='P'&&
        line[1]>='0'&&line[1]<='9'&&line[2]>='0'&&line[2]<='9';
}
void show(const eii::Machine& m,double wall,const char* label){
    std::string lcd=m.lcd.line(0);
    for(auto& ch:lcd)if(ch<' '||ch==127)ch=' ';
    std::cout<<label<<" wall="<<std::fixed<<std::setprecision(2)<<wall
             <<"s virtual="<<double(m.ticks)/ticksPerSecond
             <<"s lcd="<<std::quoted(lcd)
             <<" pc=0x"<<std::hex<<m.main.cpu.pc<<std::dec
             <<" floppy_rx="<<m.diskSio.channels[0].rx.characters
             <<" read_pulses="<<(m.diskRead?m.diskRead->outputPulses:0)
             <<" hdd_read="<<(m.hardDisk?m.hardDisk->bytesRead:0)
             <<" midi_reads="<<m.midiSerial.reads
             <<" mem_writes="<<m.dramWriteCycles
             <<std::endl;
}
}

int main(int argc,char** argv)try{
    if(argc!=3){
        std::cerr<<"usage: original_eii_private_boot_probe <ROM-directory> <original-floppy.emuiifd>\n";
        return 2;
    }
    const std::filesystem::path folder=argv[1];
    const auto disk=std::filesystem::path(argv[2]);
    // Exact VST3 plugin boot power-on configuration; no firmware shortcuts.
    auto m=std::make_unique<eii::Machine>(0);
    m->load(folder/"main.bin",folder/"scanner.bin",
            folder/"ic135.bin",folder/"ic137.bin");
    m->installSecondBank(false);
    m->initializeDramPowerOn(1);
    m->enableProductionController(true);
    m->initializeControllerPowerOn(0xe1122026u);
    auto bytes=eii::readFile(disk);
    if(bytes.size()>=8&&std::equal(bytes.begin(),bytes.begin()+8,"HXCPICFE"))
        bytes=eii::HfeImage(std::move(bytes)).extractEmuii();
    auto media=std::make_shared<eii::EmuiiImage>(std::move(bytes));
    m->floppy.attach(0,37,400000);
    m->floppy.drives[0]->insertSensorDisk(false);
    m->diskRead=std::make_unique<eii::DiskReadPath>(87,8,m->ticks);
    m->diskRead->mountWritable(0,media,eii::EmuiiGap::Hxc2026);
    m->diskRead->persistTrack=[](unsigned,unsigned,unsigned,
                                 std::span<const std::uint8_t>){return false;};
    m->diskDma.floppyIo=true;
    m->enableNormalRuntime();

    // Same basic voice renderer as the plugin, not a sampled fake instrument.
    std::uint64_t frames=0,noteNonzero=0;
    double peak=0,energy=0;
    bool noteStarted=false;
    m->enableRuntimeAudio([&](auto block){
        frames+=block.size();
        if(noteStarted)for(const auto& f:block){
            const auto level=std::max(std::abs(f.left),std::abs(f.right));
            peak=std::max(peak,double(level));
            energy+=double(f.left)*f.left+double(f.right)*f.right;
            if(level>1e-8f)++noteNonzero;
        }
    },eii::analog::RuntimeAudioMode::BasicVoice);

    const auto start=Clock::now();
    std::uint64_t nextLog=ticksPerSecond;
    show(*m,seconds(start),"BOOT_BEGIN");
    while(!playable(*m)&&m->ticks<std::uint64_t(maxVirtualSeconds)*ticksPerSecond){
        m->run(quantum); // exactly every original Z80/DRAM/DMA/SIO tick
        if(m->ticks>=nextLog){
            show(*m,seconds(start),"BOOT_PROGRESS");
            nextLog=m->ticks+ticksPerSecond;
        }
        if(seconds(start)>maxWallSeconds){
            show(*m,seconds(start),"BOOT_WALL_TIMEOUT");
            return 3; // never report fake playable firmware
        }
    }
    if(!playable(*m)){
        show(*m,seconds(start),"BOOT_VIRTUAL_TIMEOUT");
        return 4;
    }
    show(*m,seconds(start),"BOOT_FIRST_PLAYABLE_PXX");
    if(!m->midiSerial.enabled()){
        std::cerr<<"BOOT reached Pxx but original firmware MIDI UART is not enabled\n";
        return 5;
    }
    const std::array<std::uint8_t,3> on{0x90,60,100};
    if(!m->receiveMidi(on))throw std::runtime_error("Original UART rejected NoteOn 60");
    noteStarted=true;
    m->run(2*ticksPerSecond);
    const std::array<std::uint8_t,3> off{0x80,60,0};
    m->receiveMidi(off);
    m->run(ticksPerSecond);
    std::cout<<"ORIGINAL_AUDIO_RESULT wall="<<seconds(start)
             <<"s sample_frames="<<frames<<" active_nonzero="<<noteNonzero
             <<" peak="<<std::setprecision(12)<<peak
             <<" energy="<<energy
             <<" midi_received="<<m->midiSerial.received
             <<" midi_reads="<<m->midiSerial.reads
             <<" midi_overruns="<<m->midiSerial.overruns
             <<" original_cpu_ticks="<<m->ticks<<std::endl;
    if(noteNonzero==0||peak<=1e-9||m->midiSerial.reads<6){
        std::cerr<<"Booted firmware, but original NoteOn/PCM not yet verified\n";
        return 6;
    }
    std::cout<<"PASS: PRIVATE original ROM + original disk booted to Pxx and produced firmware MIDI/PCM\n";
    return 0;
}catch(const std::exception& e){
    std::cerr<<"PRIVATE_BOOT_PROBE_FAILED: "<<e.what()<<'\n';
    return 7;
}
