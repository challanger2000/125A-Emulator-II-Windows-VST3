// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Firmware-owned WAV capture operator: only real EII scanner-button contacts.
// No raw DRAM writes, bank/preset fabrication or synthetic firmware responses.
// All methods are called on the VST3 machine-owner thread (never process()).
#include <cstdint>
#include <string_view>

namespace eii::wav {
enum class CaptureAction {
    None, SampleDown, SampleUp, ArmForceDown, ForceUp, StopDown, StopUp
};
enum class CapturePhase {
    Idle, SampleHeld, AwaitSample, ForceHeld, AwaitFirstRead, Recording,
    StopHeld, AwaitGood, ExitHeld, AwaitPreset, Complete, Failed
};
struct CaptureStep {
    CaptureAction action=CaptureAction::None;
    const char* error=nullptr;
    bool completed=false;
    bool success=false;
};
class FirmwareCapture {
public:
    static constexpr std::uint64_t ticksPerSecond=4000000ull;
    static constexpr std::uint64_t holdTicks=ticksPerSecond/10; // 100 ms debounce
    static constexpr std::uint64_t maxDuration=10*ticksPerSecond; // preliminary 512KiB bound
    CaptureStep begin(std::uint64_t tick,std::uint64_t durationTicks)noexcept {
        reset();
        if(durationTicks==0||durationTicks>maxDuration)
            return fail("WAV length not supported in P003 (0..10 seconds only).");
        duration_=durationTicks;phase_=CapturePhase::SampleHeld;
        deadline_=tick+holdTicks;
        return {CaptureAction::SampleDown};
    }
    CaptureStep advance(std::uint64_t tick,std::string_view lcd0,
                        std::string_view lcd1,std::uint64_t reads,
                        bool sourceStarted,std::uint64_t sourceStartTick,
                        bool sampleMode)noexcept {
        if(!active())return {};
        if(contains(lcd0,"Need More Room")||contains(lcd1,"Need More Room"))
            return fail("Firmware reports Need More Room; previous RAM not cleared.");
        if(contains(lcd0,"Sample Overload")||contains(lcd1,"Sample Overload"))
            return fail("Firmware reports Sample Overload; reduce WAV/input gain.");
        switch(phase_){
        case CapturePhase::SampleHeld:
            if(tick>=deadline_){phase_=CapturePhase::AwaitSample;deadline_=tick+45*ticksPerSecond;return {CaptureAction::SampleUp};}
            break;
        case CapturePhase::AwaitSample:
            if(sampleMode && (contains(lcd0,"VOICE V")||contains(lcd1,"VOICE V"))){
                phase_=CapturePhase::ForceHeld;baselineReads_=reads;
                deadline_=tick+holdTicks;return {CaptureAction::ArmForceDown};
            }
            if(tick>=deadline_)return fail("SAMPLE overlay did not become ready. OS 3.1 system floppy required.");
            break;
        case CapturePhase::ForceHeld:
            if(tick>=deadline_){phase_=CapturePhase::AwaitFirstRead;deadline_=tick+2*ticksPerSecond;return {CaptureAction::ForceUp};}
            break;
        case CapturePhase::AwaitFirstRead:
            if(sourceStarted&&reads>baselineReads_){
                phase_=CapturePhase::Recording;
                deadline_=sourceStartTick+duration_+ticksPerSecond/20; // 50 ms silent tail
                if(tick>=deadline_){phase_=CapturePhase::StopHeld;deadline_=tick+holdTicks;return {CaptureAction::StopDown};}
            } else if(tick>=deadline_)return fail("Original firmware did not start reading ADC after FORCE.");
            break;
        case CapturePhase::Recording:
            if(tick>=deadline_){
                if(reads<=baselineReads_)return fail("ADC never delivered sample bytes.");
                phase_=CapturePhase::StopHeld;deadline_=tick+holdTicks;return {CaptureAction::StopDown};
            }
            break;
        case CapturePhase::StopHeld:
            if(tick>=deadline_){phase_=CapturePhase::AwaitGood;deadline_=tick+8*ticksPerSecond;return {CaptureAction::StopUp};}
            break;
        case CapturePhase::AwaitGood:
            if(contains(lcd0,"Sample is good")||contains(lcd1,"Sample is good")){
                phase_=CapturePhase::ExitHeld;deadline_=tick+holdTicks;
                return {CaptureAction::SampleDown};
            }
            if(tick>=deadline_)return fail("STOP was not acknowledged by firmware as Sample is good.");
            break;
        case CapturePhase::ExitHeld:
            if(tick>=deadline_){phase_=CapturePhase::AwaitPreset;deadline_=tick+20*ticksPerSecond;return {CaptureAction::SampleUp};}
            break;
        case CapturePhase::AwaitPreset:
            if(!sampleMode && preset(lcd0)){
                phase_=CapturePhase::Complete;
                return {CaptureAction::None,nullptr,true,true};
            }
            if(tick>=deadline_)return fail("Recorded voice exists, but firmware did not return to preset mode.");
            break;
        default:break;
        }
        return {};
    }
    void reset()noexcept {phase_=CapturePhase::Idle;deadline_=duration_=baselineReads_=0;}
    bool active()const noexcept{return phase_!=CapturePhase::Idle&&phase_!=CapturePhase::Complete&&phase_!=CapturePhase::Failed;}
    CapturePhase phase()const noexcept{return phase_;}
    const char* stageName()const noexcept {
        switch(phase_){
        case CapturePhase::SampleHeld:case CapturePhase::AwaitSample:return "Loading original SAMPLE module";
        case CapturePhase::ForceHeld:case CapturePhase::AwaitFirstRead:return "Firmware FORCE / ADC start";
        case CapturePhase::Recording:return "Recording through original EII SAR";
        case CapturePhase::StopHeld:case CapturePhase::AwaitGood:return "Firmware STOP / capture verification";
        case CapturePhase::ExitHeld:case CapturePhase::AwaitPreset:return "Returning to playable preset";
        case CapturePhase::Complete:return "Firmware capture complete (RAM only)";
        case CapturePhase::Failed:return "Firmware capture failed";
        default:return "Idle";
        }
    }
private:
    CapturePhase phase_=CapturePhase::Idle;
    std::uint64_t deadline_=0,duration_=0,baselineReads_=0;
    static bool contains(std::string_view s,std::string_view needle)noexcept{
        return s.find(needle)!=std::string_view::npos;
    }
    static bool preset(std::string_view s)noexcept{
        return s.size()>=3 && s[0]=='P' && s[1]>='0'&&s[1]<='9' && s[2]>='0'&&s[2]<='9';
    }
    CaptureStep fail(const char* why)noexcept{
        phase_=CapturePhase::Failed;return {CaptureAction::None,why,true,false};
    }
};
} // namespace eii::wav
