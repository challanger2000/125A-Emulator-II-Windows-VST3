// SPDX-License-Identifier: GPL-3.0-only
#include "125a_bank_save.h"
#include <cstdlib>
#include <iostream>
using namespace eii::portable;
void req(bool good,const char* why){if(!good){std::cerr<<"FAIL "<<why<<"\n";std::exit(1);}}
int main(){
    const auto t=FirmwareBankSave::rate,h=FirmwareBankSave::hold;
    FirmwareBankSave s;
    auto action=s.begin(0,12);
    req(action.action==SaveAction::DiskDown,"physical DISK pressed");
    req(s.advance(h,"P01 NULL PRESET","",12,0,true).action==SaveAction::DiskUp,"DISK release");
    req(s.advance(2*h,"Disk [1-8]","",12,0,true).action==SaveAction::SaveDown,"original SAVE BANK key 7");
    req(s.advance(3*h,"Disk [1-8]","",12,0,true).action==SaveAction::SaveUp,"release save");
    req(s.advance(4*h,"Save Bank to","Drive 1? Y/N",12,0,true).action==SaveAction::YesDown,"original yes key9");
    req(s.advance(5*h,"This Will Take","A While",16,0,false).action==SaveAction::YesUp,"release yes");
    req(s.advance(40*t,"This Will Take","A While",100,0,false).action==SaveAction::None,"must not truncate partial track write");
    auto out=s.advance(71*t,"Disk [1-8]","",149,0,true);
    req(out.action==SaveAction::ExitDown,"137 track writes accepted only once firmware returns");
    req(s.advance(71*t+h,"Disk [1-8]","",149,0,true).action==SaveAction::ExitUp,"exit DISK module");
    out=s.advance(72*t,"P01 NULL PRESET","",149,0,true);
    req(out.done&&out.ok&&!s.active(),"firmware save accepted on Pxx");
    s.begin(0,0);s.advance(h,"P01","",0,0,true);
    out=s.advance(10*t,"P01","",0,0,true);
    req(out.done&&!out.ok,"missing original disk menu fails");
    s.begin(0,0);s.advance(h,"P01","",0,0,true);
    out=s.advance(2*h,"Disk [1-8]","",0,1,true);
    req(out.done&&!out.ok,"floppy write error fails");
    s.begin(0,0);s.advance(h,"P01","",0,0,true);
    s.advance(2*h,"Disk [1-8]","",0,0,true);
    s.advance(3*h,"Disk [1-8]","",0,0,true);
    out=s.advance(10*t,"Disk [1-8]","",0,0,true);
    req(out.done&&!out.ok,"missing save prompt fails");
    s.begin(0,0);s.advance(h,"P01","",0,0,true);
    s.advance(2*h,"Disk [1-8]","",0,0,true);
    s.advance(3*h,"Disk [1-8]","",0,0,true);
    s.advance(4*h,"Save Bank to","Drive 1? Y/N",0,0,true);
    s.advance(5*h,"This Will Take","A While",4,0,false);
    out=s.advance(126*t,"Disk [1-8]","",120,0,true);
    req(out.done&&!out.ok,"incomplete fewer than 130 tracks fails");
    // P041: a swallowed original DISK exit contact is retried only while the
    // actual firmware LCD stays in the DISK menu; Pxx remains mandatory.
    auto advanceToExit=[&](){
        s.begin(0,12);
        s.advance(h,"P01 NULL PRESET","",12,0,true);
        s.advance(2*h,"Disk [1-8]","",12,0,true);
        s.advance(3*h,"Disk [1-8]","",12,0,true);
        s.advance(4*h,"Save Bank to","Drive 1? Y/N",12,0,true);
        s.advance(5*h,"This Will Take","A While",16,0,false);
        req(s.advance(71*t,"Disk [1-8]","",149,0,true).action==SaveAction::ExitDown,
            "P041 exit pulse after full track write");
        req(s.advance(71*t+h,"Disk [1-8]","",149,0,true).action==SaveAction::ExitUp,
            "P041 release original DISK contact");
    };
    advanceToExit();
    out=s.advance(80*t,"Disk [1-8]","",149,0,true);
    req(out.action==SaveAction::ExitDown&&!out.done,"P041 first bounded exit retry");
    req(s.advance(80*t+h,"Disk [1-8]","",149,0,true).action==SaveAction::ExitUp,
        "P041 retry releases original DISK contact");
    out=s.advance(81*t,"P01 NULL PRESET","",149,0,true);
    req(out.done&&out.ok,"P041 missed exit recovers only on actual Pxx");
    advanceToExit();
    for(int attempt=0;attempt<2;++attempt){
        const auto when=(80+9*attempt)*t;
        out=s.advance(when,"Disk [1-8]","",149,0,true);
        req(out.action==SaveAction::ExitDown&&!out.done,
            "P041 bounded menu exit retry allowed");
        req(s.advance(when+h,"Disk [1-8]","",149,0,true).action==SaveAction::ExitUp,
            "P041 bounded menu retry released");
    }
    out=s.advance(98*t,"Disk [1-8]","",149,0,true);
    req(out.done&&!out.ok,"P041 never accepts bank save without Pxx");
    advanceToExit();
    out=s.advance(80*t,"Unexpected firmware screen","",149,0,true);
    req(out.done&&!out.ok,"P041 unrelated firmware screen must fail closed");
    std::cout<<"P004 original-firmware DISK7 SAVEBANK acceptance/error FSM PASS\n";
}
