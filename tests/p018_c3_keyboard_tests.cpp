// SPDX-License-Identifier: GPL-3.0-only
#include "125a_wav_c3_keyboard.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
using eii::portable::WavC3Keyboard;
static void require(bool b,const char* message){if(!b){std::cerr<<"FAIL P018: "<<message<<"\n";std::exit(1);}}
static std::array<std::uint8_t,3> msg(int status,int note,int vel){return {
    std::uint8_t(status),std::uint8_t(note),std::uint8_t(vel)};}
int main(){
    WavC3Keyboard a,b;
    require(WavC3Keyboard::hostRoot==60&&WavC3Keyboard::originalRoot==48,
            "explicit Studio One MIDI60/original MIDI48 distinction");
    auto m=msg(0x90,60,127);
    require(a.remap(m,3,true)&&m[1]==48&&m[2]==127,
            "C3 MIDI60 NoteOn routes into original EII MIDI48 without velocity change");
    m=msg(0x80,60,64);
    require(a.remap(m,3,true)&&m[1]==48&&m[2]==64,
            "C3 NoteOff releases original MIDI48");
    m=msg(0x91,72,30);
    require(a.remap(m,3,true)&&m[1]==60,
            "channel 2 MIDI72 maps by one octave");
    m=msg(0x81,72,40);
    require(a.remap(m,3,true)&&m[1]==60,"second channel noteoff releases original note");
    m=msg(0x90,60,99);
    require(b.remap(m,3,false)&&m[1]==60,
            "unrelated VST3 instance and factory EII banks retain unshifted note");
    m=msg(0x80,60,0);
    require(b.remap(m,3,false)&&m[1]==60,"unshifted bank NoteOff remains original");
    m=msg(0x90,59,101);
    require(a.remap(m,3,true)&&m[1]==47,"below C3 maps chromatically");
    m=msg(0x90,59,120);
    require(a.remap(m,3,false)&&m[1]==47,
            "duplicate NoteOn after menu toggle cannot change held mapping");
    m=msg(0x80,59,12);
    require(a.remap(m,3,false)&&m[1]==47,
            "NoteOff after disabling map still releases the actual old key");
    m=msg(0x90,50,70);
    require(a.remap(m,3,false)&&m[1]==50,"new note after menu change unshifted");
    m=msg(0x90,50,0);
    require(a.remap(m,3,true)&&m[1]==50,
            "velocity-zero note-off after menu change uses held mapping");
    m=msg(0x91,60,70);
    require(a.remap(m,3,true)&&m[1]==48,"second channel held");
    m=msg(0xb1,123,0);
    require(a.remap(m,3,true)&&m[1]==123,"CC123 forwards unchanged");
    m=msg(0x81,60,0);
    require(a.remap(m,3,false)&&m[1]==60,"CC123 cleared old note mapping");
    m=msg(0x90,0,100);
    require(!a.remap(m,3,true),"negative transpose out of MIDI range must be dropped");
    m=msg(0x80,0,0);
    require(!a.remap(m,3,true),"unmapped out-of-range NoteOff dropped");
    m=msg(0x90,127,100);
    require(a.remap(m,3,true)&&m[1]==115,"upper key still playable when C3");
    m=msg(0xe0,20,80);
    require(a.remap(m,3,true)&&m==msg(0xe0,20,80),"pitch bend unchanged");
    m=msg(0xb0,64,127);
    require(a.remap(m,3,true)&&m==msg(0xb0,64,127),"sustain pedal unchanged");
    m=msg(0xc0,33,0);
    require(a.remap(m,2,true)&&m[1]==33,"program change unchanged");
    a.reset();
    m=msg(0x80,127,0);
    require(a.remap(m,3,false)&&m[1]==127,"new firmware boot resets held-note state");
    std::cout<<"P018 Studio One C3 MIDI60 -> original EII MIDI48, release/toggle/isolation PASS\n";
}
