// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P034: RT-safe channel-voice MIDI parser driven solely by completed original
// SCN2651 UART TX bytes. This is NOT an on-note echo or firmware shortcut.
// VST3 lacks a generic raw MIDI 1.0 byte event; unsupported system messages
// must never be fabricated as channel notes.
#include <array>
#include <cstdint>

namespace eii::vst::midiout {
struct Byte {
    std::uint8_t value=0;
    std::uint64_t epoch=0,generation=0,frame=0;
};
struct Message {
    std::uint8_t status=0,data1=0,data2=0;
    unsigned size=0;
};
class Assembler {
public:
    void reset()noexcept {running_=0;first_=0;have_=0;sysEx_=false;}
    bool feed(std::uint8_t c,Message& out)noexcept {
        // Timing clock, start/stop and active sensing may appear between the
        // two data bytes of a channel message: they NEVER cancel running status.
        if(c>=0xf8){++unsupportedRealtime;return false;}
        if(sysEx_){
            if(c==0xf7){sysEx_=false;++unsupportedSystem;}
            else ++skippedSysExBytes;
            return false; // malformed channel statuses cannot escape a SysEx
        }
        if(c&0x80){
            if(c>=0xf0){
                // SysEx and system common are deliberately not mapped to
                // invalid VST3 channel events. F7 terminates SysEx.
                sysEx_=c==0xf0;running_=0;have_=0;
                ++unsupportedSystem;return false;
            }
            running_=c;sysEx_=false;have_=0;return false;
        }
        if(sysEx_){++skippedSysExBytes;return false;}
        if(running_==0){++orphanData;return false;}
        const auto type=running_&0xf0;
        if(type==0xc0||type==0xd0){
            out={running_,c,0,2};++completed;return true;
        }
        if(have_==0){first_=c;have_=1;return false;}
        out={running_,first_,c,3};have_=0;++completed;return true;
    }
    std::uint64_t completed=0,orphanData=0,unsupportedSystem=0,
                  unsupportedRealtime=0,skippedSysExBytes=0;
private:
    std::uint8_t running_=0,first_=0;
    unsigned have_=0;bool sysEx_=false;
};
} // namespace eii::vst::midiout
