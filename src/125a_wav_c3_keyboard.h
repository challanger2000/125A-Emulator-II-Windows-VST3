// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P018: optional HOST MIDI keyboard display convention for WAV imports.
// External MIDI 60 (Studio One C3) plays EII original MIDI 48 without
// modifying the original E-mu firmware, RAM, pitch table or bank format.
// Owner thread only; one independent instance per emulated machine.
#include <algorithm>
#include <array>
#include <cstdint>

namespace eii::portable {
class WavC3Keyboard {
public:
    static constexpr int hostRoot=60;
    static constexpr int originalRoot=48;
    static constexpr int difference=originalRoot-hostRoot; // -12 semitones
    WavC3Keyboard()noexcept{reset();}
    void reset()noexcept{
        for(auto& channel:held_)channel.fill(-1);
    }
    // True = event can be sent unmodified or rewritten to original MIDI;
    // false = out-of-range host key, intentionally dropped rather than
    // clamped to the wrong playable EII pitch.
    bool remap(std::array<std::uint8_t,3>& data,unsigned size,bool c3)noexcept {
        if(size!=3)return true;
        const auto status=data[0]&0xf0u;
        const auto channel=std::size_t(data[0]&0x0fu);
        if(status==0xb0u&&(data[1]==120||data[1]==123)){
            held_[channel].fill(-1); // firmware all-sound-off/all-notes-off
            return true;
        }
        if(status!=0x80u&&status!=0x90u)return true;
        const auto note=std::size_t(data[1]);
        if(note>=128)return false;
        auto& assigned=held_[channel][note];
        const bool noteOn=(status==0x90u&&data[2]>0);
        if(noteOn){
            // Repeated NoteOn retains the prior mapping until a matching
            // NoteOff. A GUI octave toggle cannot strand an active voice.
            if(assigned<0){
                const int mapped=int(note)+(c3?difference:0);
                if(mapped<0||mapped>127)return false;
                assigned=std::int16_t(mapped);
            }
            data[1]=std::uint8_t(assigned);
            return true;
        }
        const int mapped=assigned>=0?assigned:int(note)+(c3?difference:0);
        assigned=-1;
        if(mapped<0||mapped>127)return false;
        data[1]=std::uint8_t(mapped);
        return true;
    }
private:
    std::array<std::array<std::int16_t,128>,16> held_{};
};
} // namespace eii::portable
