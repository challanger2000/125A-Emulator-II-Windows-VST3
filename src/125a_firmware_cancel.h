// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Non-destructive cancellation of firmware-owned EII SAMPLE input.
// Only scanner keys and observed original firmware mode/LCD are used.
// Hardware time still runs normally. No synthetic firmware or memory writes.
#include <cstdint>
#include <string_view>

namespace eii::wav {
enum class CancelAction { None, StopDown, StopUp, SampleDown, SampleUp };
enum class CancelPhase { Idle, Settling, StopHeld, AwaitStop, ExitHeld, AwaitPreset, Complete, Failed };
struct CancelStep {
    CancelAction action=CancelAction::None;
    const char* error=nullptr;
    bool done=false,ok=false;
};
class FirmwareCancel {
public:
    static constexpr std::uint64_t rate=4000000ull;
    static constexpr std::uint64_t hold=rate/10;
    CancelStep begin(std::uint64_t tick) noexcept {
        reset();phase_=CancelPhase::Settling;
        deadline_=tick+45*rate;settleUntil_=tick+rate/4;
        return {};
    }
    CancelStep advance(std::uint64_t tick,bool known,bool sampleMode,
                       std::string_view lcd0,std::string_view lcd1,bool diskIdle) noexcept {
        if(!active())return {};
        if(tick>=deadline_)return fail("Original SAMPLE recovery timed out; reset manually before changing disks.");
        const bool playable=known&&!sampleMode&&preset(lcd0)&&diskIdle;
        const bool good=contains(lcd0,"Sample is good")||contains(lcd1,"Sample is good");
        const bool voice=contains(lcd0,"VOICE V")||contains(lcd1,"VOICE V");
        switch(phase_) {
        case CancelPhase::Settling:
            if(playable){phase_=CancelPhase::Complete;return {CancelAction::None,nullptr,true,true};}
            if(tick<settleUntil_||!known)return {};
            if(!sampleMode)return {}; // Wait while firmware loads SAMPLE, do not guess.
            if(good||voice)return startExit(tick);
            phase_=CancelPhase::StopHeld;settleUntil_=tick+hold;
            return {CancelAction::StopDown};
        case CancelPhase::StopHeld:
            if(tick>=settleUntil_){phase_=CancelPhase::AwaitStop;return {CancelAction::StopUp};}
            break;
        case CancelPhase::AwaitStop:
            if(playable){phase_=CancelPhase::Complete;return {CancelAction::None,nullptr,true,true};}
            if(known&&sampleMode&&(good||voice))return startExit(tick);
            break;
        case CancelPhase::ExitHeld:
            if(tick>=settleUntil_){phase_=CancelPhase::AwaitPreset;return {CancelAction::SampleUp};}
            break;
        case CancelPhase::AwaitPreset:
            if(playable){phase_=CancelPhase::Complete;return {CancelAction::None,nullptr,true,true};}
            break;
        default:break;
        }
        return {};
    }
    void reset()noexcept{phase_=CancelPhase::Idle;deadline_=settleUntil_=0;}
    bool active()const noexcept {
        return phase_!=CancelPhase::Idle&&phase_!=CancelPhase::Complete&&phase_!=CancelPhase::Failed;
    }
    CancelPhase phase()const noexcept{return phase_;}
    const char* label()const noexcept {
        switch(phase_) {
        case CancelPhase::Settling:return "WAV cancel: waiting for original SAMPLE firmware";
        case CancelPhase::StopHeld:case CancelPhase::AwaitStop:return "WAV cancel: original firmware STOP";
        case CancelPhase::ExitHeld:case CancelPhase::AwaitPreset:return "WAV cancel: returning to Pxx";
        case CancelPhase::Complete:return "WAV cancelled and original firmware recovered";
        case CancelPhase::Failed:return "WAV cancellation needs manual firmware recovery";
        default:return "Idle";
        }
    }
private:
    CancelPhase phase_=CancelPhase::Idle;
    std::uint64_t deadline_=0,settleUntil_=0;
    static bool contains(std::string_view text,std::string_view sub)noexcept {
        return text.find(sub)!=std::string_view::npos;
    }
    static bool preset(std::string_view text)noexcept{
        return text.size()>=3&&text[0]=='P'&&text[1]>='0'&&text[1]<='9'&&text[2]>='0'&&text[2]<='9';
    }
    CancelStep startExit(std::uint64_t tick)noexcept{
        phase_=CancelPhase::ExitHeld;settleUntil_=tick+hold;
        return {CancelAction::SampleDown};
    }
    CancelStep fail(const char* reason)noexcept {
        phase_=CancelPhase::Failed;return {CancelAction::None,reason,true,false};
    }
};
} // namespace eii::wav
