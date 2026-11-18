// SPDX-License-Identifier: GPL-3.0-only
#include "125a_firmware_cancel.h"
#include <cstdlib>
#include <iostream>
using namespace eii::wav;
static void need(bool x,const char* s){if(!x){std::cerr<<"FAIL "<<s<<"\n";std::exit(1);}}
int main(){
    const auto H=FirmwareCancel::hold, T=FirmwareCancel::rate;
    FirmwareCancel c;
    auto s=c.begin(0);need(c.active()&&s.action==CancelAction::None,"begin safe wait");
    s=c.advance(T/8,true,false,"Loading overlay","",true);
    need(!s.done&&s.action==CancelAction::None,"do not press STOP before sample firmware");
    s=c.advance(T/4,true,true,"Record in progress","",true);
    need(s.action==CancelAction::StopDown,"STOP once original SAMPLE active");
    s=c.advance(T/4+H,true,true,"Record in progress","",true);
    need(s.action==CancelAction::StopUp,"release STOP key");
    s=c.advance(T/4+2*H,true,true,"Sample is good","",true);
    need(s.action==CancelAction::SampleDown,"exit original SAMPLE after STOP");
    s=c.advance(T/4+3*H,true,true,"Sample is good","",true);
    need(s.action==CancelAction::SampleUp,"release SAMPLE");
    s=c.advance(T/4+4*H,true,false,"P01 Choir","",false);
    need(!s.done,"never restore disk while physical disk is busy");
    s=c.advance(T/4+5*H,true,false,"P01 Choir","",true);
    need(s.done&&s.ok&&!c.active(),"cancel completes only on idle playable firmware");
    c.reset();
    c.begin(0);
    s=c.advance(T/4,true,true,"VOICE V 01","",true);
    need(s.action==CancelAction::SampleDown,"armed but not recording: direct SAMPLE exit");
    s=c.advance(T/4+H,true,true,"VOICE V 01","",true);
    need(s.action==CancelAction::SampleUp,"direct exit release");
    s=c.advance(T/4+2*H,true,false,"P03","",true);
    need(s.done&&s.ok,"nonrecording cancel returned to preset");
    c.begin(0);
    s=c.advance(T/4,true,false,"P01","",true);
    need(s.done&&s.ok,"pre-firmware cancel already in performance mode");
    c.begin(0);
    s=c.advance(T/4,false,false,"Unknown","",true);
    need(!s.done&&s.action==CancelAction::None,"unknown mode cannot guess key");
    s=c.advance(46*T,false,false,"Unknown","",true);
    need(s.done&&!s.ok&&c.phase()==CancelPhase::Failed,"unknown mode fail closed timeout");
    c.reset();
    need(!c.active(),"reset recovery state");
    std::cout<<"P011 original-firmware STOP/SAMPLE cancellation FSM: PASS\n";
}
