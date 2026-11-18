// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Owner-thread preboot event policy: preserve host automation; never queue
// old MIDI note times into the original EII before it has its first Pxx.
#include <cstdint>
namespace eii::portable {
enum class PrebootEventAction:std::uint8_t { DropMidi, ApplyControl, DropUnknown };
constexpr PrebootEventAction prebootAction(std::uint8_t kind)noexcept {
    return kind==0?PrebootEventAction::DropMidi:
           kind==1?PrebootEventAction::ApplyControl:
                   PrebootEventAction::DropUnknown;
}
// The original HD PROM starts without the optional floppy inserted and
// scans the drive once the original OS has reached its RAM-resident region.
constexpr bool insertDelayedFloppy(bool held,std::uint16_t mainPc)noexcept {
    return held&&mainPc>=0x2800u;
}
} // namespace eii::portable
