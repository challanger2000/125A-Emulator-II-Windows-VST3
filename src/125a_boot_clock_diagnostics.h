// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P020: measure ORIGINAL Emulator II startup using independent wall and
// machine/host clocks. Instrumentation only: no firmware, PCM, Z80, disk,
// MIDI or DAW timeline modification; values originate on the owner thread.
#include <algorithm>
#include <cstdint>

namespace eii::portable {

enum class BootStage : std::uint8_t {
    Idle, Booting, ReadingMedia, AwaitingHostClock, EmulationBehind,
    Ready, Failed
};

struct BootClockSnapshot {
    BootStage stage=BootStage::Idle;
    std::uint64_t wallMs=0,virtualTicks=0;
    std::uint64_t floppyBytes=0,hddBytes=0;
    std::uint64_t hostInactiveMs=0,emulatorInactiveMs=0;
    // 1000 = 100% of real-time emulated clock (4 MHz).
    unsigned realtimePermille=0;
    bool complete=false;
};

inline const char* bootStageName(BootStage s)noexcept {
    switch(s){
        case BootStage::Idle:return "Not started";
        case BootStage::Booting:return "Original firmware booting";
        case BootStage::ReadingMedia:return "Original floppy/HDD transfer";
        case BootStage::AwaitingHostClock:return "WAIT: DAW audio clock not advancing";
        case BootStage::EmulationBehind:return "WAIT: emulator CPU is behind DAW clock";
        case BootStage::Ready:return "Original firmware displays playable Pxx";
        case BootStage::Failed:return "Original firmware boot failed";
    }
    return "Unknown";
}

class BootClockDiagnostics {
public:
    static constexpr std::uint64_t cpuHz=4000000ull;
    static constexpr std::uint64_t hostStallWarningMs=2000;
    static constexpr std::uint64_t ownerStallWarningMs=2000;

    void reset()noexcept{*this=BootClockDiagnostics{};}
    void begin(std::uint64_t wallMs,std::uint64_t machineTicks,
               std::uint64_t hostTicks,std::uint64_t floppyBytes=0,
               std::uint64_t hddBytes=0)noexcept{
        reset();
        running_=true;startedMs_=lastHostMoveMs_=lastMachineMoveMs_=wallMs;
        startTicks_=lastTicks_=machineTicks;
        lastHostTicks_=hostTicks;
        startFloppy_=lastFloppy_=floppyBytes;
        startHdd_=lastHdd_=hddBytes;
        data_.stage=BootStage::Booting;
    }
    BootClockSnapshot observe(std::uint64_t nowMs,std::uint64_t machineTicks,
                              std::uint64_t hostTicks,std::uint64_t floppyBytes,
                              std::uint64_t hddBytes,bool presetDisplayed,
                              bool diskBusy,bool emulatorFailed=false)noexcept {
        if(!running_)return data_;
        if(data_.complete)return data_; // freeze actual time-to-Pxx
        if(nowMs<startedMs_)nowMs=startedMs_;
        if(hostTicks!=lastHostTicks_){
            lastHostTicks_=hostTicks;
            lastHostMoveMs_=nowMs;
        }
        if(machineTicks!=lastTicks_){
            lastTicks_=machineTicks;
            lastMachineMoveMs_=nowMs;
        }
        const bool diskMoved=floppyBytes>lastFloppy_||hddBytes>lastHdd_;
        lastFloppy_=floppyBytes;
        lastHdd_=hddBytes;
        data_.wallMs=nowMs-startedMs_;
        data_.virtualTicks=machineTicks>=startTicks_?machineTicks-startTicks_:0;
        data_.floppyBytes=floppyBytes>=startFloppy_?floppyBytes-startFloppy_:0;
        data_.hddBytes=hddBytes>=startHdd_?hddBytes-startHdd_:0;
        data_.hostInactiveMs=nowMs-lastHostMoveMs_;
        data_.emulatorInactiveMs=nowMs-lastMachineMoveMs_;
        if(data_.wallMs){
            const auto seconds=double(data_.virtualTicks)/double(cpuHz);
            const auto speed=seconds*1000000.0/double(data_.wallMs);
            data_.realtimePermille=unsigned(std::min(100000.0,speed));
        }
        if(emulatorFailed){
            data_.stage=BootStage::Failed;
            data_.complete=true;
        }else if(presetDisplayed){
            data_.stage=BootStage::Ready;
            data_.complete=true;
        }else if(data_.emulatorInactiveMs>=ownerStallWarningMs &&
                 data_.hostInactiveMs>=hostStallWarningMs){
            // A stopped DAW transport or suspended process callback can
            // prevent boot progression in the existing host-paced engine.
            // This is NOT evidence of slow Z80 instructions or broken ROM.
            data_.stage=BootStage::AwaitingHostClock;
        }else if(data_.emulatorInactiveMs>=ownerStallWarningMs &&
                 data_.hostInactiveMs<hostStallWarningMs){
            data_.stage=BootStage::EmulationBehind;
        }else if(diskBusy||diskMoved){
            data_.stage=BootStage::ReadingMedia;
        }else{
            data_.stage=BootStage::Booting;
        }
        return data_;
    }
    BootClockSnapshot snapshot()const noexcept{return data_;}
private:
    BootClockSnapshot data_{};
    bool running_=false;
    std::uint64_t startedMs_=0,lastHostMoveMs_=0,lastMachineMoveMs_=0;
    std::uint64_t startTicks_=0,lastTicks_=0,lastHostTicks_=0;
    std::uint64_t startFloppy_=0,lastFloppy_=0,startHdd_=0,lastHdd_=0;
};
} // namespace eii::portable
