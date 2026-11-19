#include "125a_original_midi_out.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
using eii::vst::midiout::Assembler;
using eii::vst::midiout::Message;
static void require(bool x,const char* reason){if(!x)throw std::runtime_error(reason);}
int main()try{
    Assembler a;Message msg{};
    require(!a.feed(48,msg)&&a.orphanData==1,"data without original TX status rejected");
    require(!a.feed(0x90,msg)&&!a.feed(60,msg),"three byte MIDI note incomplete");
    require(!a.feed(0xF8,msg)&&!a.feed(0xFE,msg),"realtime bytes ignored without breaking running status");
    require(a.feed(100,msg)&&msg.status==0x90&&msg.data1==60&&msg.data2==100&&msg.size==3,
            "original NoteOn completed after two data bytes");
    require(!a.feed(62,msg)&&a.feed(127,msg)&&msg.status==0x90&&msg.data1==62&&msg.data2==127,
            "running status preserves following note");
    require(!a.feed(0x80,msg)&&!a.feed(62,msg)&&a.feed(23,msg)&&msg.status==0x80&&msg.data2==23,
            "original NoteOff release velocity preserved");
    require(!a.feed(0xC3,msg)&&a.feed(7,msg)&&msg.status==0xC3&&msg.data1==7&&msg.size==2,
            "original ProgramChange is two bytes");
    require(a.feed(8,msg)&&msg.status==0xC3&&msg.data1==8,"running status for ProgramChange");
    require(!a.feed(0xD1,msg)&&a.feed(83,msg)&&msg.status==0xD1&&msg.data1==83,
            "original ChannelPressure two bytes");
    require(!a.feed(0xE2,msg)&&!a.feed(0x7f,msg)&&a.feed(0x3f,msg)&&
            msg.status==0xE2&&msg.data1==127&&msg.data2==63,"original PitchBend 14bit preserved");
    require(!a.feed(0xA1,msg)&&!a.feed(50,msg)&&a.feed(49,msg)&&
            msg.status==0xA1&&msg.data1==50&&msg.data2==49,"original PolyPressure");
    require(!a.feed(0xB5,msg)&&!a.feed(64,msg)&&a.feed(127,msg)&&
            msg.status==0xB5&&msg.data1==64&&msg.data2==127,"original CC sustain");
    require(!a.feed(0xF0,msg)&&!a.feed(0x90,msg)&&!a.feed(0xF0,msg)&&
            !a.feed(0x01,msg)&&!a.feed(0x02,msg)&&!a.feed(0xF8,msg)&&
            !a.feed(0xF7,msg)&&!a.feed(64,msg),"SysEx/system common not fabricated as notes");
    require(!a.feed(0xF2,msg)&&!a.feed(0x05,msg)&&!a.feed(0x07,msg),
            "system-common bytes not silently represented as channel events");
    require(!a.feed(0x90,msg)&&!a.feed(60,msg),"new note pending");
    a.reset();require(!a.feed(127,msg),"generation reset erases incomplete MIDI and running status");
    require(!a.feed(0x90,msg)&&!a.feed(60,msg)&&a.feed(0,msg)&&msg.data2==0,
            "velocity-zero original NoteOn emitted for downstream NoteOff conversion");
    require(a.completed==11,"exactly 11 reconstructed channel messages, no fake system events");
    require(a.unsupportedRealtime==3,"three original realtime messages counted");
    require(a.unsupportedSystem==4,"F0,F0,F7,F2 system events counted");
    std::cout<<"P034 original SCN2651 MIDI OUT parser channel voice, running status,"
             " realtime interruption, SysEx/system guards, reset PASS\n";
}catch(const std::exception& e){std::cerr<<"P034 FAIL "<<e.what()<<'\n';return 1;}
