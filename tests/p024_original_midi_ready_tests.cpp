// SPDX-License-Identifier: GPL-3.0-only
#include "125a_original_midi_ready.h"
#include <cstdlib>
#include <iostream>
using eii::portable::firmwarePlayable;
static void expect(bool v,const char* why){
    if(!v){std::cerr<<"FAIL P024: "<<why<<"\n";std::exit(1);}
}
int main(){
    expect(!firmwarePlayable(false,false),"machine not yet at original ROM Pxx");
    expect(!firmwarePlayable(true,false),
           "private ROM first P01 at 49.01s precedes MIDI UART enable");
    expect(!firmwarePlayable(false,true),
           "UART alone without actual original Pxx cannot open audio gate");
    expect(firmwarePlayable(true,true),
           "private firmware at P01 EII Choir + original MIDI UART enables correct playback");
    std::cout<<"P024 original first Pxx AND real SCN2651 MIDI ready host handoff PASS\n";
}
