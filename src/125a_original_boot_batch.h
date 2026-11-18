// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P019: first-boot machine-owner batching, NEVER skipped emulated clocks.
// All time-critical MIDI events continue to cut a batch at their exact tick.
#include <cstdint>

namespace eii::portable {
class OriginalBootBatch {
public:
    static constexpr std::uint64_t cpuHz=4000000ull;
    static constexpr std::uint64_t quantumNormal=20000ull; // 5ms
    static constexpr std::uint64_t quantumFine=4000ull; // 1ms
    static constexpr std::uint64_t dspBlock=8000ull; // 2ms
    static constexpr std::uint64_t normalDsp=3*dspBlock;
    static constexpr std::uint64_t bootBasic=3*quantumNormal; // 15ms
    static constexpr std::uint64_t bootDsp=6*dspBlock; // 12ms, whole 96-frame DSP blocks
    void reset()noexcept{bootDone_=false;batched_=0;}
    void ready()noexcept{bootDone_=true;}
    bool isReady()const noexcept{return bootDone_;}
    std::uint64_t batched()const noexcept{return batched_;}
    std::uint64_t quantum(bool dsp,bool urgent,bool samplingOrProjectWrite)noexcept {
        if(urgent)return dsp?dspBlock:quantumFine;
        if(bootDone_||samplingOrProjectWrite)return dsp?normalDsp:quantumNormal;
        ++batched_;
        return dsp?bootDsp:bootBasic;
    }
private:
    bool bootDone_=true; // no boost until explicit original machine reset
    std::uint64_t batched_=0;
};
} // namespace eii::portable
