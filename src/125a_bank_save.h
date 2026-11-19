// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P004 original EII firmware DISK 7 SAVE BANK controller.
// Only emulated physical buttons and observed firmware LCD + actual disk
// write counters. Never fabricates bank headers, RAM or disk sectors.
#include <cstdint>
#include <string_view>
namespace eii::portable {
enum class SaveAction{None,DiskDown,DiskUp,SaveDown,SaveUp,YesDown,YesUp,ExitDown,ExitUp};
enum class SavePhase{Idle,EnterHeld,AwaitDisk,SaveHeld,AwaitPrompt,YesHeld,Writing,
                     ExitHeld,AwaitPreset,Complete,Failed};
struct SaveStep{SaveAction action=SaveAction::None;const char* error=nullptr;bool done=false,ok=false;};
class FirmwareBankSave {
public:
    static constexpr std::uint64_t rate=4000000,hold=rate/10,maxSave=120*rate;
    // Original scanner contacts may occasionally miss a DISK exit pulse.
    // Retry only while the firmware LCD still explicitly shows the DISK menu.
    static constexpr unsigned maxExitRetries=2;
    SaveStep begin(std::uint64_t tick,std::uint64_t writes)noexcept{
        reset();startWrites_=writes;phase_=SavePhase::EnterHeld;deadline_=tick+hold;
        return {SaveAction::DiskDown};
    }
    SaveStep advance(std::uint64_t tick,std::string_view lcd0,std::string_view lcd1,
                     std::uint64_t writes,std::uint64_t writeErrors,bool mediaIdle)noexcept{
        if(!active())return {};
        if(writeErrors)return fail("Original floppy writer reported an error");
        switch(phase_){
        case SavePhase::EnterHeld:
            if(tick>=deadline_){phase_=SavePhase::AwaitDisk;deadline_=tick+8*rate;return {SaveAction::DiskUp};}
            break;
        case SavePhase::AwaitDisk:
            if(lcd0.find("Disk [1-8]")!=lcd0.npos){
                phase_=SavePhase::SaveHeld;deadline_=tick+hold;return {SaveAction::SaveDown};
            }
            if(tick>=deadline_)return fail("Original DISK menu did not open");
            break;
        case SavePhase::SaveHeld:
            if(tick>=deadline_){phase_=SavePhase::AwaitPrompt;deadline_=tick+8*rate;return {SaveAction::SaveUp};}
            break;
        case SavePhase::AwaitPrompt:
            if(lcd0.find("Save Bank to")!=lcd0.npos&&lcd1.find("Drive 1? Y/N")!=lcd1.npos){
                phase_=SavePhase::YesHeld;deadline_=tick+hold;return {SaveAction::YesDown};
            }
            if(tick>=deadline_)return fail("Original SAVE BANK confirmation not recognized");
            break;
        case SavePhase::YesHeld:
            if(tick>=deadline_){phase_=SavePhase::Writing;deadline_=tick+maxSave;return {SaveAction::YesUp};}
            break;
        case SavePhase::Writing:
            // P004 original OS 3.1 proof: 137 tracks written. A complete
            // image save must involve >=130 distinct original track writes;
            // fewer can be a prematurely interrupted firmware transaction.
            if(writes>=startWrites_+130&&mediaIdle&&lcd0.find("Disk [1-8]")!=lcd0.npos){
                phase_=SavePhase::ExitHeld;deadline_=tick+hold;return {SaveAction::ExitDown};
            }
            if(tick>=deadline_)return fail("Original firmware bank write incomplete/timed out");
            break;
        case SavePhase::ExitHeld:
            if(tick>=deadline_){phase_=SavePhase::AwaitPreset;deadline_=tick+8*rate;return {SaveAction::ExitUp};}
            break;
        case SavePhase::AwaitPreset:
            if(lcd0.size()>=3&&lcd0[0]=='P'&&lcd0[1]>='0'&&lcd0[1]<='9'&&lcd0[2]>='0'&&lcd0[2]<='9'){
                phase_=SavePhase::Complete;return {SaveAction::None,nullptr,true,true};
            }
            if(tick>=deadline_){
                // Do not declare a bank saved while still inside DISK.
                // Re-send a bounded physical DISK contact if the original
                // menu is clearly still displayed; all other states fail.
                if(lcd0.find("Disk [1-8]")!=lcd0.npos&&exitRetries_<maxExitRetries){
                    ++exitRetries_;
                    phase_=SavePhase::ExitHeld;deadline_=tick+hold;
                    return {SaveAction::ExitDown};
                }
                return fail("Saved bank not returned to Pxx performance screen");
            }
            break;
        default:break;
        }
        return {};
    }
    bool active()const noexcept{return phase_!=SavePhase::Idle&&phase_!=SavePhase::Complete&&phase_!=SavePhase::Failed;}
    SavePhase phase()const noexcept{return phase_;}
    const char* label()const noexcept{
        switch(phase_){
        case SavePhase::EnterHeld:case SavePhase::AwaitDisk:return "Opening original EII DISK module";
        case SavePhase::SaveHeld:case SavePhase::AwaitPrompt:return "Selecting DISK 7 SAVE BANK";
        case SavePhase::YesHeld:return "Confirming protected in-memory performance bank";
        case SavePhase::Writing:return "Original floppy controller writing complete bank";
        case SavePhase::ExitHeld:case SavePhase::AwaitPreset:return "Closing original disk menu";
        case SavePhase::Complete:return "Original EII bank saved";
        case SavePhase::Failed:return "Original EII bank save failed";
        default:return "Idle";
        }
    }
    void reset()noexcept{phase_=SavePhase::Idle;startWrites_=deadline_=0;exitRetries_=0;}
private:
    SavePhase phase_=SavePhase::Idle;
    std::uint64_t startWrites_=0,deadline_=0;
    unsigned exitRetries_=0;
    SaveStep fail(const char* why)noexcept{
        phase_=SavePhase::Failed;return {SaveAction::None,why,true,false};
    }
};
} // namespace eii::portable
