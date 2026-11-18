// SPDX-License-Identifier: GPL-3.0-only
#include "125a_original_firmware_midi_ready.h"
#include <cstdlib>
#include <iostream>
using eii::portable::originalFirmwareMidiReady;
static void test(bool ok,const char* reason){
    if(!ok){std::cerr<<"FAIL P024: "<<reason<<"\n";std::exit(1);}
}
int main(){
    test(!originalFirmwareMidiReady(false,false),
         "boot ROM splash cannot expose DAW note playback");
    test(!originalFirmwareMidiReady(false,true),
         "SCN2651 alone without loaded preset cannot release audio gate");
    test(!originalFirmwareMidiReady(true,false),
         "AUTHENTIC PRIVATE ROM: P01 appears before original UART is enabled");
    test(originalFirmwareMidiReady(true,true),
         "real original P01 EII Choir + SCN2651 = DAW MIDI is safe to release");
    std::cout<<"P024 verified two-stage real original firmware Pxx/SCN2651 readiness policy PASS\n";
}
