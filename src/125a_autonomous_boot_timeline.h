// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P021: hardware ticks run independently of a stopped DAW audio clock
// ONLY while genuine firmware is not yet at the playable Pxx display.
// This is an owner-thread scheduler, not a substitute firmware/ROM/OS.
#include <algorithm>
#include <cstdint>

namespace eii::portable {
class AutonomousBootTimeline {
public:
    static constexpr std::uint64_t cpuHz=4000000;
    static constexpr std::uint64_t maxBootTicks=240*cpuHz;
    // A previous original ROM/HDD startup exceeded 130 s. The wall watchdog
    // must never mistake that for a failed guest boot.
    static constexpr std::uint64_t maxBootWallMs=300000;
    void begin(std::uint64_t virtualTick,std::uint64_t wallMs)noexcept {
        booting_=true;startVirtual_=virtualTick;startWall_=wallMs;
    }
    bool active()const noexcept{return booting_;}
    bool exceeded(std::uint64_t virtualTick,std::uint64_t nowMs)const noexcept{
        return booting_&&((virtualTick>=startVirtual_&&virtualTick-startVirtual_>=maxBootTicks)||
            (nowMs>=startWall_&&nowMs-startWall_>=maxBootWallMs));
    }
    // Run Machine::run for EVERY original clock tick, even when the host
    // target is zero or the host transport doesn't call process().
    static constexpr std::uint64_t quantum(bool nonlinear)noexcept {
        return nonlinear?48000:60000;
    }
    void handoff(std::uint64_t guestTick,std::uint64_t hostPos)noexcept{
        booting_=false;anchorVirtual_=guestTick;anchorHostPos_=hostPos;
    }
    std::uint64_t anchoredTarget(std::uint64_t hostPos,std::uint32_t rate)const noexcept{
        if(rate==0||hostPos<=anchorHostPos_)return anchorVirtual_;
        return anchorVirtual_+(hostPos-anchorHostPos_)*cpuHz/rate;
    }
    std::int64_t relativeFrame(std::uint64_t hostPos,std::int64_t latency)const noexcept{
        const auto pos=std::int64_t(hostPos);
        return pos-std::int64_t(anchorHostPos_)-latency;
    }
    std::uint64_t anchorHostPos()const noexcept{return anchorHostPos_;}
    std::uint64_t anchorVirtual()const noexcept{return anchorVirtual_;}
private:
    bool booting_=false;
    std::uint64_t startVirtual_=0,startWall_=0;
    std::uint64_t anchorVirtual_=0,anchorHostPos_=0;
};
} // namespace eii::portable
